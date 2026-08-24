import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="IndustrialCarbonForecasting"
)

cursor = connection.cursor()

cursor.execute("SELECT DATABASE();")

print("Connected Database:", cursor.fetchone()[0])

cursor.execute("SHOW TABLES")

print("\nTables:")

for table in cursor:
    print(table[0])

connection.close()