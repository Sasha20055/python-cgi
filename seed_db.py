# seed_db.py
import sqlite3

conn = sqlite3.connect("./ecomap.db")
cursor = conn.cursor()

# Добавим пользователя
cursor.execute("INSERT INTO User (username, email, password) VALUES (?, ?, ?)",
               ("eco_user", "eco@example.com", "hashed_password"))

user_id = cursor.lastrowid

# Добавим место
cursor.execute("INSERT INTO Location (name, address, latitude, longitude, addedBy) VALUES (?, ?, ?, ?, ?)",
               ("Свалка №1", "ул. Примерная, д. 1", 55.75, 37.61, user_id))

location_id = cursor.lastrowid

# Добавим тип отходов
cursor.execute("INSERT INTO WasteType (name, description) VALUES (?, ?)",
               ("Пластик", "Пластиковые отходы"))

waste_type_id = cursor.lastrowid

# Связка место-отход
cursor.execute("INSERT INTO LocationWaste (locationId, wasteTypeId) VALUES (?, ?)",
               (location_id, waste_type_id))

# Отзыв
cursor.execute("INSERT INTO Review (userId, locationId, rating, comment) VALUES (?, ?, ?, ?)",
               (user_id, location_id, 5, "Очень загрязнённое место, требует уборки."))

conn.commit()
print("Данные успешно добавлены.")
conn.close()