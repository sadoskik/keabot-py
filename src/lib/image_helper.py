import sqlite3
from sqlite3 import Connection, Cursor, Row
from pathlib import Path
from typing import Optional


def get_random_image(conn: Connection, server_id: int, tag: str) -> Optional[Path]:
    cursor = conn.cursor()
    cursor: Cursor
    res = cursor.execute(
            """SELECT i.file_path
            FROM image i
            JOIN image_tag it ON i.id = it.image_id
            JOIN tag t ON it.tag_id = t.id
            WHERE i.server_id = :server_id
                AND t.name = :tag
                AND t.server_id = i.server_id
            ORDER BY RANDOM();""",
            {
                "server_id": server_id,
                "tag": tag
            }
            )
    row:Row = res.fetchone()
    cursor.close()
    if not row:
        return None
    return Path(row["file_path"])

def add_tag(conn: Connection, server_id: int, tag: str) -> str:
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR IGNORE INTO tag (name, server_id) VALUES (:name, :server_id);""",
        {
            "server_id": server_id,
            "name": tag
        }
    )
    conn.commit()
    cursor.close()

def check_tag(conn: Connection, server_id: int, tag: str)->bool:
    cursor = conn.cursor()
    cursor.execute('''
            SELECT id FROM tag WHERE name = ? AND server_id = ?
        ''', (tag, server_id))
    row = cursor.fetchone()
    cursor.close()
    if not row:
        return False
    return True

def get_tags(conn: Connection, server_id: int) -> list[str]:
    cursor = conn.cursor()
    # Step 1: Retrieve all tags for the given server_id
    cursor.execute('''
        SELECT name FROM tag WHERE server_id = ?
    ''', (server_id,))

    # Step 2: Fetch all the results
    tags = cursor.fetchall()
    # Step 4: Return the list of tags (if any) as a list of tag names
    return [tag[0] for tag in tags]
    
def add_image(conn: Connection, server_id: int, tags: list[str], filename: str):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO image (file_path, server_id)
        VALUES (?, ?)
    ''', (str(filename), server_id))

    # Get the ID of the newly inserted image
    image_id = cursor.lastrowid

    # Step 2: Insert each tag into the 'tag' table if it doesn't already exist
    for tag_name in tags:
        if not check_tag(conn, server_id, tag_name):
            add_tag(conn, server_id, tag_name)

        # Step 3: Get the tag_id for the inserted tag (whether newly inserted or existing)
        cursor.execute('''
            SELECT id FROM tag WHERE name = ? AND server_id = ?
        ''', (tag_name, server_id))
        tag_id = cursor.fetchone()[0]

        # Step 4: Create the many-to-many relationship in the 'image_tag' table
        cursor.execute('''
            INSERT INTO image_tag (image_id, tag_id)
            VALUES (?, ?)
        ''', (image_id, tag_id))
    conn.commit()
    cursor.close()