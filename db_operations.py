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

def get_song_counts(group_id, record_date=None):
    cur = get_db().cursor()

    if record_date is None:
        return cur.execute("SELECT title, count(*) AS count FROM recordings WHERE group_id = ? GROUP BY lower(title);", [group_id]).fetchall()
    else:
        return cur.execute("SELECT title, count(*) AS count FROM recordings WHERE group_id = ? AND record_date = ? GROUP BY lower(title);", [group_id, record_date]).fetchall()


def record_upload(filename, event_time, size, etag, group_id, record_date:str='', tags:str=None):
    db = get_db()
    cur = db.cursor()
  
    try:
        cur.execute(
            """
                INSERT INTO recordings(
                    filename,
                    upload_date,
                    size,
                    etag,
                    group_id,
                    record_date,
                    tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                
            """,
            [filename, event_time, size, etag, group_id, record_date, tags]
        )
        db.commit()

    except Exception as e:
        print("")
        print("An error occurred while recording an upload.")
        print(e)


def get_single_thing(filename):
    cur = get_db().cursor()
    print(quote(filename))
    
    cur.execute('SELECT * FROM recordings WHERE filename like ?;', [f'{filename.replace(" ", "+")}_%'])    
    return cur.fetchone()


def get_song_names(group_id: int):
    cur = get_db().cursor()

    cur.execute("""
        SELECT
            name,
            recording_count
        FROM songs2
        LEFT JOIN (
            SELECT
                title,
                count(*) AS recording_count
            FROM
                recordings
            WHERE
                group_id = ?
            GROUP BY lower(title)
        ) ON name = title
        WHERE
            songs2.group_id = ?
        ORDER BY name ASC;
    """, [group_id, group_id])
    return cur.fetchall()

def add_new_song(group_id: int, title: str):
    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
            SELECT name
            FROM songs2
            WHERE lower(name) = lower(trim(?))
                AND group_id = ?
            LIMIT 1;
        """,
        [title, group_id]
    )

    if cur.fetchone() is not None:
        return -1

    cur.execute("""
        INSERT INTO songs2 (name, group_id)
        VALUES (?, ?);
    """, [title, group_id])

    db.commit()

    return 0

def update_track(id, description, title, date, recorded_by, location, tags, partial=None):
    db = get_db()
    cur = db.cursor()

    if bool(partial) == True:
        if tags.strip() == '': 
            tags = 'partial'
        else: 
            tags = ','.join(tags.split(',') + ['partial'])

    cur.execute("""
        UPDATE recordings
        SET
            description = ?,
            title = ?,
            record_date = ?,
            recorded_by = ?,
            location = ?,
            tags = ?
        WHERE
            id = ?;
    """, [
        description,
        title,
        date,
        recorded_by,
        location,
        tags.lower(),
        id
    ])
    
    db.commit()

def get_group_info(group_id):
    cur = get_db().cursor()
    return cur.execute("SELECT * FROM groups WHERE id = ?;", [group_id]).fetchone()


def list_all_things(group_id):
    db = get_db()
    cur = db.cursor()
  
    try:
        cur.execute("""
            SELECT *
            FROM recordings
            WHERE group_id = ?;
        """, [group_id])
        rows = cur.fetchall()
        return rows

    except Exception as e:
        print("An error occurred fetching all of the things.")
        print(e)


def list_things_on_date(group_id, record_date):
    db = get_db()
    cur = db.cursor()
  
    try:
        cur.execute("""
            SELECT *
            FROM recordings
            WHERE group_id = ?
                AND record_date = ?;
        """, [group_id, record_date])
        rows = cur.fetchall()
        return rows

    except Exception as e:
        print("An error occurred fetching all of the things.")
        print(e)


def search_for_things(tag, group_id):
    db = get_db()
    cur = db.cursor()
    try:
        return cur.execute("""
            SELECT *
            FROM recordings
            WHERE instr(tags, ?)
            AND group_id = ?
            ;
        """,
        [tag, group_id])
    except Exception as e:
        print("An error occurred searching for things.")
        print(e)

def search_for_song(song, group_id):
    db = get_db()
    cur = db.cursor()
    try:
        return cur.execute("""
            SELECT *
            FROM recordings
            WHERE trim(lower(title)) = trim(lower(?))
            AND group_id = ?
        """,
        [song, group_id])
    except Exception as e:
        print("An error occurred searching for a song.")
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
    db.commit()

    return x[0]
