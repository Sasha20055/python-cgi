#!/usr/bin/env python3
import sqlite3
import json
import cgi
import cgitb
import os
import sys

cgitb.enable()

def send_cors_headers():
    print("Access-Control-Allow-Origin: *")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")

def respond_with_json(data):
    send_cors_headers()
    print("Content-Type: application/json\n")
    print(json.dumps(data, ensure_ascii=False, indent=2))

method = os.environ.get("REQUEST_METHOD", "GET")

# Handle OPTIONS request early
if method == "OPTIONS":
    send_cors_headers()
    print("Content-Type: application/json\n")
    print(json.dumps({"status": "ok"}))
    sys.exit(0)

# Path to your SQLite DB
db_path = "/Users/aleksandrnikolenko/programming/python-unik/ecomap/ecomap.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

data = {}

try:
    if method == "GET":
        form = cgi.FieldStorage()
        query_type = form.getfirst("queryType", "")

        if query_type == "location_rating":
            cursor.execute("""
                SELECT L.name, AVG(R.rating)
                FROM Location L
                LEFT JOIN Review R ON L.id = R.locationId
                GROUP BY L.id
            """)
            data = [{"location": row[0], "average_rating": float(row[1] or 0)} for row in cursor.fetchall()]

        elif query_type == "location_count":
            cursor.execute("SELECT COUNT(*) FROM Location")
            count = cursor.fetchone()[0]
            data = {"location_count": count}

        elif query_type == "user_count":
            cursor.execute("SELECT COUNT(*) FROM User")
            count = cursor.fetchone()[0]
            data = {"user_count": count}

        elif query_type == "review_count":
            cursor.execute("SELECT COUNT(*) FROM Review")
            count = cursor.fetchone()[0]
            data = {"review_count": count}

        elif query_type == "comments_by_location":
            cursor.execute("""
                SELECT L.name, COUNT(R.comment)
                FROM Location L
                LEFT JOIN Review R ON L.id = R.locationId
                WHERE R.comment IS NOT NULL
                GROUP BY L.id
            """)
            data = [{"location": row[0], "comments": row[1]} for row in cursor.fetchall()]

        elif query_type == "tag_usage":
            cursor.execute("""
                SELECT T.name, COUNT(*) as usage_count
                FROM Tag T
                JOIN LocationTag LT ON T.id = LT.tagId
                GROUP BY T.id
            """)
            data = [{"tag": row[0], "used": row[1]} for row in cursor.fetchall()]

        elif query_type == "all_locations":
            cursor.execute("SELECT id, name, address, latitude, longitude, addedBy FROM Location")
            data = [
                {
                    "id": row[0],
                    "name": row[1],
                    "address": row[2],
                    "latitude": row[3],
                    "longitude": row[4]
                }
                for row in cursor.fetchall()
            ]

        else:
            data = {"error": f"Invalid queryType: {query_type}"}

    elif method == "POST":
        content_length = int(os.environ.get("CONTENT_LENGTH", 0))
        if content_length == 0:
            respond_with_json({"error": "Empty request body"})
            sys.exit(0)

        post_data = sys.stdin.read(content_length)
        try:
            body = json.loads(post_data)
        except json.JSONDecodeError as e:
            respond_with_json({"error": "Invalid JSON", "details": str(e)})
            sys.exit(0)
        body = json.loads(post_data)
        action = body.get("action")

        if action == "add_user":
            cursor.execute("""
                INSERT INTO User (username, email, password)
                VALUES (?, ?, ?)
            """, (body["username"], body["email"], body["password"]))
            conn.commit()
            data = {"success": True, "user_id": cursor.lastrowid}

        elif action == "add_location":
            cursor.execute("""
                INSERT INTO Location (name, address, latitude, longitude, addedBy)
                VALUES (?, ?, ?, ?, ?)
            """, (body["name"], body["address"], body["latitude"], body["longitude"], body["addedBy"]))
            conn.commit()
            data = {"success": True, "location_id": cursor.lastrowid}

        elif action == "add_waste_type":
            cursor.execute("""
                INSERT INTO WasteType (name, description)
                VALUES (?, ?)
            """, (body["name"], body.get("description", "")))
            conn.commit()
            data = {"success": True, "waste_type_id": cursor.lastrowid}

        elif action == "add_review":
            cursor.execute("""
                INSERT INTO Review (userId, locationId, rating, comment)
                VALUES (?, ?, ?, ?)
            """, (body["userId"], body["locationId"], body["rating"], body.get("comment", "")))
            conn.commit()
            data = {"success": True, "review_id": cursor.lastrowid}

        else:
            data = {"error": f"Invalid action: {action}"}

except sqlite3.OperationalError as e:
    data = {"error": f"SQL error: {str(e)}"}
except Exception as e:
    data = {"error": f"Unexpected error: {str(e)}"}

conn.close()
respond_with_json(data)