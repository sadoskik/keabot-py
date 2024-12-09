import sqlite3
from pathlib import Path
import sys

def initialize_database(db_name: Path):
    # Connect to SQLite database (it will create the database if it doesn't exist)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create 'image' table to store file paths and server IDs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            server_id TEXT NOT NULL
        )
    ''')

    # Create 'tag' table to store unique tag names and associated server IDs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            server_id TEXT NOT NULL,
            UNIQUE(name, server_id)  -- Ensures unique combinations of 'name' and 'server_id'
        )
    ''')

    # Create 'image_tag' table to represent the many-to-many relationship between 'image' and 'tag'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_tag (
            image_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            FOREIGN KEY (image_id) REFERENCES image(id),
            FOREIGN KEY (tag_id) REFERENCES tag(id),
            PRIMARY KEY (image_id, tag_id)
        )
    ''')

    # Create 'user' table to store user scores with unique server_id and user_id combination
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            score INTEGER NOT NULL,
            given INTEGER NOT NULL,
            self INTEGER NOT NULL,
            UNIQUE(server_id, user_id)  -- Ensures unique combinations of 'server_id' and 'user_id'
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database(sys.argv[1])