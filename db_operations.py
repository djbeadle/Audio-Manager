import sqlite3
from flask import g, current_app
from urllib.parse import quote


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


def get_single_thing(filename):
    cur = get_db().cursor()
    print(quote(filename))
    
    cur.execute('SELECT * FROM recordings WHERE filename = ?;', [filename.replace(' ', '+')])    
    return cur.fetchone()


def get_song_names():
    cur = get_db().cursor()

    cur.execute('SELECT name FROM songs;')
    return cur.fetchall()

def update_track(id, description, title, date, recorder, tags):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        UPDATE recordings
        SET
            description = ?,
            title = ?,
            record_date = ?,
            -- recorder = ?,
            tags = ?
        WHERE
            id = ?;
    """, [
        description, title, date,
        #recorder,
        tags, id])
    
    db.commit()
    db.close()

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


def get_next_asset_id():
    """
    Each file that is attempted to be uploaded is given a unique ID to ensure files with duplicate names do not overwrite each other.
    """
    db = get_db()
    cur = db.cursor()

    cur.execute("BEGIN;")
    cur.execute("UPDATE asset_counter SET asset_id = asset_id + 1 WHERE rowid = 1;")
    cur.execute('SELECT asset_id - 1 FROM asset_counter WHERE rowid = 1')
    x = cur.fetchone()
    cur.execute('COMMIT;')

    return x[0]