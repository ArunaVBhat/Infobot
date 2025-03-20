import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'new_users.db')

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            usn TEXT NOT NULL
        )
    ''')
    conn.commit()
    print("Users table has been created successfully.")
    conn.close()

if __name__ == '__main__':
    init_db()