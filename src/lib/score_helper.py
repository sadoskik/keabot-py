import sqlite3
from sqlite3 import Connection, Cursor, Row
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def check_user(conn: Connection, server_id:int, user_id: int) -> bool:
    cursor = conn.cursor()
    res = cursor.execute(
            "SELECT * FROM user WHERE user_id=:user_id AND server_id=:server_id",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    if res.fetchone() is None:
        conn.commit()
        cursor.close()
        return False
    else:
        conn.commit()
        cursor.close()
        return True

def add_user(conn: Connection, server_id:int, user_id: int):
    logger.info("Adding user %d to server %d", user_id, server_id)
    cursor = conn.cursor()
    cursor.execute(
            """INSERT INTO user (user_id, server_id, score, self, given)
            VALUES (:user_id, :server_id, 0, 0, 0);""",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    conn.commit()
    cursor.close()


def increment_score(conn: Connection, server_id: int, user_id: int):
    logger.info("Incrementing score for user %d in server %d", user_id, server_id)
    if not check_user(conn, server_id, user_id):
        add_user(conn, server_id, user_id)
    cursor = conn.cursor()
    cursor.execute(
            """UPDATE user
            SET score = score + 1
            WHERE server_id = :server_id AND user_id = :user_id;""",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    conn.commit()
    cursor.close()

def decrement_score(conn: Connection, server_id: int, user_id: int):
    logger.info("Decrementing score for user %d in server %d", user_id, server_id)
    if not check_user(conn, server_id, user_id):
        add_user(conn, server_id, user_id)
    cursor = conn.cursor()
    cursor.execute(
            """UPDATE user
            SET score = score - 1
            WHERE server_id = :server_id AND user_id = :user_id;""",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    conn.commit()
    cursor.close()

def get_score(conn: Connection, server_id: int, user_id: int) -> int:
    if not check_user(conn, server_id, user_id):
        add_user(conn, server_id, user_id)
    cursor = conn.cursor()
    res = cursor.execute(
            """SELECT score FROM user
            WHERE server_id = :server_id AND user_id = :user_id;""",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    row:Row = res.fetchone()
    conn.commit()
    cursor.close()
    return row["score"]

def get_server_scores(conn: Connection, server_id: int) -> list[Row]:
    cursor = conn.cursor()
    res = cursor.execute(
            """SELECT score FROM user
            WHERE server_id = :server_id;""",
            {
                "server_id": server_id,
            }
            )
    scores = res.fetchall()
    conn.commit()
    cursor.close()
    return scores

def get_top_scores(conn: Connection, server_id: int, num:int=5) -> list[Row]:
    logger.info("Getting top %d scores for server %d", num, server_id)
    cursor = conn.cursor()
    res = cursor.execute(
            """SELECT score, user_id FROM user
            WHERE server_id = :server_id
            ORDER BY score DESC;""",
            {
                "server_id": server_id,
            }
            )
    scores:list[Row] = res.fetchmany(num)
    conn.commit()
    cursor.close()
    return scores

def increment_self(conn: Connection, server_id: int, user_id: int):
    logger.info("Incrementing self for user %d in server %d", user_id, server_id)
    if not check_user(conn, server_id, user_id):
        add_user(conn, server_id, user_id)
    cursor = conn.cursor()
    cursor.execute(
            """UPDATE user
            SET self = self + 1
            WHERE server_id = :server_id AND user_id = :user_id;""",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    conn.commit()
    cursor.close() 

def decrement_self(conn: Connection, server_id: int, user_id: int):
    logger.info("Decrementing self for user %d in server %d", user_id, server_id)
    if not check_user(conn, server_id, user_id):
        add_user(conn, server_id, user_id)
    cursor = conn.cursor()
    cursor.execute(
            """UPDATE user
            SET self = self - 1
            WHERE server_id = :server_id AND user_id = :user_id;""",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    conn.commit()
    cursor.close()

def increment_given(conn: Connection, server_id: int, user_id: int):
    logger.info("Incrementing given for user %d in server %d", user_id, server_id)
    if not check_user(conn, server_id, user_id):
        add_user(conn, server_id, user_id)
    cursor = conn.cursor()
    cursor.execute(
            """UPDATE user
            SET given = given + 1
            WHERE server_id = :server_id AND user_id = :user_id;""",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    conn.commit()
    cursor.close()    

def decrement_given(conn: Connection, server_id: int, user_id: int):
    logger.info("Decrementing given for user %d in server %d", user_id, server_id)
    if not check_user(conn, server_id, user_id):
        add_user(conn, server_id, user_id)
    cursor = conn.cursor()
    cursor.execute(
            """UPDATE user
            SET given = given - 1
            WHERE server_id = :server_id AND user_id = :user_id;""",
            {
                "server_id": server_id,
                "user_id": user_id
            }
            )
    conn.commit()
    cursor.close()
