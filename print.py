import sqlite3

conn = sqlite3.connect('net_devs.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM devices')
data = cursor.fetchall()

# Print the data
print("devices:")
for row in data:
    print(row)

cursor.execute('SELECT * FROM previous_devices')
data = cursor.fetchall()

# Print the data
print("previous_devices:")
for row in data:
    print(row)

# Close the connection
conn.close()
