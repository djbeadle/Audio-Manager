import sqlite3
from flask import g, current_app

def get_db():
    """
    Singleton for database connection
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config['DB_NAME'])
        db.row_factory = sqlite3.Row
    return db


def record_upload(filename, event_time, size, etag):
    db = get_db()
    cur = db.cursor()
  
    try:
        cur.execute(
            """
                INSERT INTO recordings(
                    filename,
                    upload_date,
                    size,
                    etag
                ) VALUES (?, ?, ?, ?);
                
            """,
            [filename, event_time, size, etag]
        )
        rows = cur.fetchall()
        db.commit()
        db.close()
        return rows

    except Exception as e:
        print("")
        print("An error occurred fetching all of the things.")
        print(e)


def list_all_things():
    db = get_db()
    cur = db.cursor()
  
    try:
        cur.execute("""
            SELECT id, filename, record_date, description, status, tags
            FROM recordings;
        """)
        rows = cur.fetchall()
        db.commit()
        db.close()
        return rows

    except Exception as e:
        print("An error occurred fetching all of the things.")
        print(e)

def search_for_things(tag):
    db = get_db()
    cur = db.cursor()
    try:
        return cur.execute("""
            SELECT id, filename, record_date, description, status, tags
            FROM recordings
            WHERE instr(tags, ?);
        """,
        [tag])
    except Exception as e:
        print("An error occurred searching for things.")
        print(e)
