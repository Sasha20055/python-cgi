#!/usr/bin/env python3
import sqlite3
import json
import cgi
import cgitb
import os
import sys

cgitb.enable()

DB_PATH = "/Users/aleksandrnikolenko/programming/python-unik/ecomap/ecomap.db"

def send_cors_headers():
    origin = os.environ.get("HTTP_ORIGIN", "*")
    print(f"Access-Control-Allow-Origin: {origin}")
    print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
    print("Access-Control-Allow-Headers: Content-Type")
    print("Access-Control-Allow-Credentials: true")

def respond_with_json(data):
    send_cors_headers()
    print("Content-Type: application/json\n")
    print(json.dumps(data, ensure_ascii=False, indent=2))

def fetch_all_locations(cursor):
    cursor.execute("""
        SELECT id, name, address, latitude, longitude, addedBy
        FROM Location
    """)
    return [
        {
            "id": row[0],
            "name": row[1],
            "address": row[2],
            "latitude": row[3],
            "longitude": row[4],
            "addedBy": row[5],
        }
        for row in cursor.fetchall()
    ]

def main():
    method = os.environ.get("REQUEST_METHOD", "GET")

    # Обрабатываем preflight
    if method == "OPTIONS":
        send_cors_headers()
        print("Content-Type: application/json\n")
        print(json.dumps({"status": "ok"}))
        sys.exit(0)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        data = {}
        try:
            if method == "GET":
                form = cgi.FieldStorage()
                q = form.getfirst("queryType", "")

                if q == "location_rating":
                    cursor.execute("""
                        SELECT L.name, AVG(R.rating) AS avg_rating
                        FROM Location L
                        LEFT JOIN Review R ON L.id = R.locationId
                        GROUP BY L.id
                    """)
                    data = [
                        {"location": row["name"], "average_rating": float(row["avg_rating"] or 0)}
                        for row in cursor.fetchall()
                    ]

                elif q == "location_count":
                    # Возвращаем массив локаций (аналог all_locations)
                    data = fetch_all_locations(cursor)

                elif q == "user_count":
                    cursor.execute("SELECT COUNT(*) as cnt FROM User")
                    data = {"user_count": cursor.fetchone()["cnt"]}

                elif q == "review_count":
                    cursor.execute("SELECT COUNT(*) as cnt FROM Review")
                    data = {"review_count": cursor.fetchone()["cnt"]}

                elif q == "comments_by_location":
                    cursor.execute("""
                        SELECT L.name, COUNT(R.comment) AS comments
                        FROM Location L
                        LEFT JOIN Review R ON L.id = R.locationId
                        WHERE R.comment IS NOT NULL
                        GROUP BY L.id
                    """)
                    data = [
                        {"location": row["name"], "comments": row["comments"]}
                        for row in cursor.fetchall()
                    ]

                elif q == "tag_usage":
                    cursor.execute("""
                        SELECT T.name, COUNT(*) AS usage_count
                        FROM Tag T
                        JOIN LocationTag LT ON T.id = LT.tagId
                        GROUP BY T.id
                    """)
                    data = [
                        {"tag": row["name"], "used": row["usage_count"]}
                        for row in cursor.fetchall()
                    ]

                elif q == "all_locations":
                    data = fetch_all_locations(cursor)

                else:
                    data = {"error": f"Invalid queryType: {q}"}

            elif method == "POST":
                length = int(os.environ.get("CONTENT_LENGTH", 0))
                if not length:
                    return respond_with_json({"error": "Empty request body"})

                body = json.loads(sys.stdin.read(length))
                action = body.get("action", "")

                if action == "add_user":
                    cursor.execute("""
                        INSERT INTO User (username, email, password)
                        VALUES (:username, :email, :password)
                    """, body)
                    conn.commit()
                    data = {"success": True, "user_id": cursor.lastrowid}

                elif action == "add_location":
                    cursor.execute("""
                        INSERT INTO Location (name, address, latitude, longitude, addedBy)
                        VALUES (:name, :address, :latitude, :longitude, :addedBy)
                    """, body)
                    conn.commit()
                    data = {"success": True, "location_id": cursor.lastrowid}

                elif action == "add_waste_type":
                    cursor.execute("""
                        INSERT INTO WasteType (name, description)
                        VALUES (:name, :description)
                    """, {
                        "name": body["name"],
                        "description": body.get("description", "")
                    })
                    conn.commit()
                    data = {"success": True, "waste_type_id": cursor.lastrowid}

                elif action == "add_review":
                    cursor.execute("""
                        INSERT INTO Review (userId, locationId, rating, comment)
                        VALUES (:userId, :locationId, :rating, :comment)
                    """, {
                        "userId": body["userId"],
                        "locationId": body["locationId"],
                        "rating": body["rating"],
                        "comment": body.get("comment", "")
                    })
                    conn.commit()
                    data = {"success": True, "review_id": cursor.lastrowid}

                elif action == "update_location":
                    cursor.execute("""
                        UPDATE Location
                        SET name      = :name,
                            address   = :address,
                            latitude  = :latitude,
                            longitude = :longitude,
                            addedBy   = :addedBy
                        WHERE id = :id
                    """, {
                        "id":        body["id"],
                        "name":      body["name"],
                        "address":   body["address"],
                        "latitude":  body["latitude"],
                        "longitude": body["longitude"],
                        "addedBy":   body["addedBy"]
                    })
                    conn.commit()
                    data = {
                        "success": True,
                        "updated": cursor.rowcount
                    }

                # ——— НОВОЕ: удаление локации ———
                elif action == "delete_location":
                    cursor.execute(
                        "DELETE FROM Location WHERE id = ?",
                        (body["id"],)
                    )
                    conn.commit()
                    data = {
                        "success": True,
                        "deleted": cursor.rowcount
                    }

                else:
                    data = {"error": f"Invalid action: {action}"}

        except sqlite3.OperationalError as e:
            data = {"error": f"SQL error: {e}"}
        except Exception as e:
            data = {"error": f"Unexpected error: {e}"}

    respond_with_json(data)


if __name__ == "__main__":
    main()