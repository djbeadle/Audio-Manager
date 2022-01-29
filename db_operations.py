import sqlite3
from flask import g, current_app

def get_db():
    """
    Singleton for database connection
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config['DB_NAME'])
    return db


def record_upload(filename, event_time, aws_region, source_ip, size, etag):
    db = get_db()
    cur = db.cursor()
  
    try:
        cur.execute(
            """
                INSERT INTO recordings(
                    filename,
                    event_time,
                    aws_region,
                    size,
                    etag
                ) VALUES (?, ?, ?, ?, ?);
                
            """,
            [filename, event_time, aws_region, source_ip, size, etag]
        )
        rows = cur.fetchall()
        db.commit()
        db.close()
        return rows

    except Exception as e:
        print("An error occurred fetching all of the things.")
        print(e)


def list_all_things():
    db = get_db()
    cur = db.cursor()
  
    try:
        cur.execute("""
            SELECT id, title, description, status
            FROM things;
        """)
        rows = cur.fetchall()
        db.commit()
        db.close()
        return rows

    except Exception as e:
        print("An error occurred fetching all of the things.")
        print(e)
