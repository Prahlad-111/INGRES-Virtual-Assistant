import sqlite3
from pathlib import Path


# ==================================================
# DATABASE CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "data"

DATABASE_FILE = DATABASE_DIR / "ingres_chatbot.db"


# ==================================================
# CREATE DATABASE DIRECTORY
# ==================================================

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==================================================
# INITIALIZE DATABASE
# ==================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------
    # Conversations table
    # --------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # --------------------------------------------------
    # Messages table
    # --------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            conversation_id INTEGER NOT NULL,

            role TEXT NOT NULL,

            message TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (
                conversation_id
            )
            REFERENCES conversations(id)
            ON DELETE CASCADE

        )
    """)


    connection.commit()

    connection.close()


# ==================================================
# CREATE CONVERSATION
# ==================================================

def create_conversation(
    title="New Chat"
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO conversations
        (title)

        VALUES (?)
        """,
        (title,)
    )


    conversation_id = cursor.lastrowid


    connection.commit()

    connection.close()


    return conversation_id


# ==================================================
# ADD MESSAGE
# ==================================================

def add_message(
    conversation_id,
    role,
    message
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO messages
        (
            conversation_id,
            role,
            message
        )

        VALUES (?, ?, ?)
        """,
        (
            conversation_id,
            role,
            message
        )
    )


    # Update conversation timestamp

    cursor.execute(
        """
        UPDATE conversations

        SET updated_at =
            CURRENT_TIMESTAMP

        WHERE id = ?
        """,
        (
            conversation_id,
        )
    )


    connection.commit()

    connection.close()


# ==================================================
# GET CONVERSATIONS
# ==================================================

def get_conversations():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            id,
            title,
            created_at,
            updated_at

        FROM conversations

        ORDER BY updated_at DESC
        """
    )


    conversations = [
        dict(row)
        for row in cursor.fetchall()
    ]


    connection.close()


    return conversations


# ==================================================
# GET MESSAGES
# ==================================================

def get_messages(
    conversation_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            id,
            conversation_id,
            role,
            message,
            created_at

        FROM messages

        WHERE conversation_id = ?

        ORDER BY id ASC
        """,
        (
            conversation_id,
        )
    )


    messages = [
        dict(row)
        for row in cursor.fetchall()
    ]


    connection.close()


    return messages


# ==================================================
# DELETE CONVERSATION
# ==================================================

def delete_conversation(
    conversation_id
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        DELETE FROM messages

        WHERE conversation_id = ?
        """,
        (
            conversation_id,
        )
    )


    cursor.execute(
        """
        DELETE FROM conversations

        WHERE id = ?
        """,
        (
            conversation_id,
        )
    )


    connection.commit()

    connection.close()


# ==================================================
# UPDATE CONVERSATION TITLE
# ==================================================

def update_conversation_title(
    conversation_id,
    title
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE conversations

        SET title = ?,
            updated_at =
                CURRENT_TIMESTAMP

        WHERE id = ?
        """,
        (
            title,
            conversation_id
        )
    )


    connection.commit()

    connection.close()