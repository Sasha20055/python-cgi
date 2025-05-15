# init_db.py
import sqlite3
from datetime import datetime

conn = sqlite3.connect("./ecomap.db")
cursor = conn.cursor()

# Включим поддержку внешних ключей
cursor.execute("PRAGMA foreign_keys = ON;")

# Таблица User
cursor.execute("""
CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    createdAt TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

# Таблица Location
cursor.execute("""
CREATE TABLE IF NOT EXISTS Location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    addedBy INTEGER NOT NULL,
    FOREIGN KEY (addedBy) REFERENCES User(id)
);
""")

# Таблица WasteType
cursor.execute("""
CREATE TABLE IF NOT EXISTS WasteType (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);
""")

# Таблица LocationWaste (многие-ко-многим между Location и WasteType)
cursor.execute("""
CREATE TABLE IF NOT EXISTS LocationWaste (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    locationId INTEGER NOT NULL,
    wasteTypeId INTEGER NOT NULL,
    FOREIGN KEY (locationId) REFERENCES Location(id),
    FOREIGN KEY (wasteTypeId) REFERENCES WasteType(id)
);
""")

# Таблица Review
cursor.execute("""
CREATE TABLE IF NOT EXISTS Review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    userId INTEGER NOT NULL,
    locationId INTEGER NOT NULL,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userId) REFERENCES User(id),
    FOREIGN KEY (locationId) REFERENCES Location(id)
);
""")

conn.commit()
print("Таблицы успешно созданы.")
conn.close()