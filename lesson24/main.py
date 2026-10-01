import sqlite3

connection = sqlite3.connect('example.db')

cursor = connection.cursor()

cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS email (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary REAL
    )
    '''

)

connection.commit()

query = '''
INSERT INTO email (name, department, salary) VALUES (?,?,?)
'''

cursor.execute(query, ('john', 'IT',70000.00))

connection.commit()

cursor.execute('SELECT * FROM email')

connection.commit()

rows = cursor.fetchall()

for row in rows:
    print(row)

print("UPDATED INFO\n\n")

update_query='''
UPDATE email SET salary = ? WHERE id = ?
'''

cursor.execute(update_query, (75000, 1))

connection.commit()

cursor.execute('SELECT * FROM email')

connection.commit()

rows = cursor.fetchall()

for row in rows:
    print(row)
















