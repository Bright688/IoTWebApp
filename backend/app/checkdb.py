import sqlite3

# Connect to the SQLite database (make sure the path is correct)
conn = sqlite3.connect("reports.db")
cursor = conn.cursor()

# Execute a query to retrieve report information
cursor.execute("SELECT id, email, length(pdf_data) AS pdf_size, created_at FROM reports")
rows = cursor.fetchall()

# Print the results
for row in rows:
    print(f"ID: {row[0]}, Email: {row[1]}, PDF Size: {row[2]} bytes, Created At: {row[3]}")

conn.close()