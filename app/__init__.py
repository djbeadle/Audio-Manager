from flask import Flask, Blueprint
import sqlite3

try:
  from config import config, DevelopmentConfig, ProductionConfig
except ModuleNotFoundError as e:
  print('')
  print('ERROR: You forgot to make a copy of the "config-example.py" file called "config.py"')
  print('       Your application will NOT work until you do so.')
  print('')

"""
If you have another file in this directory and want to import it you must
prefix the import statement with the directory 'app'.

ex:
from app.db_operations import create_db
"""

def create_app(config_name):
    """Application factory that returns a fully formed instance of the app

    The application context doesn't exist when this file is running, so 
    instead of being able to access values defined in the file config.py 
    the normal way as follows which uses the 'current_app' proxy:
    
    ~~~python
    from flask import current_app
    current_app.config['KEY_NAME']
    ~~~
    
    We have to manually access the config file as follows:

    ~~~python
    from config import config
    config[config_name].KEY_NAME
    ~~~
    
    Args:
      config_name (str): The name of the configuration to use
    
    """

    app = Flask(__name__, static_url_path="/static")
    print(f'The current config is "{config_name}"')

    db = sqlite3.connect(config[config_name].DB_NAME)
    cur = db.cursor()

    try:
      cur.executescript("""
        CREATE TABLE IF NOT EXISTS recordings(
          -- Fields from AWS:
          id INTEGER PRIMARY KEY,
          filename TEXT NOT NULL,
          etag TEXT NOT NULL,
          size INTEGER NOT NULL,
          upload_date TEXT DEFAULT '',
          
          -- Mandatory, non-AWS fields
          group_id INTEGER NOT NULL,

          -- User definable fields:
          title TEXT DEFAULT '', -- A display name
          version TEXT DEFAULT '', -- ex: 1, 1.4, 1.6
          recorded_by TEXT DEFAULT '', -- Who / what device recorded
          location TEXT DEFAULT '', -- Where the recording was made
          description TEXT DEFAULT '', -- ex: Notes about the song
          record_date TEXT DEFAULT '',
          tags TEXT DEFAULT '', -- A comma-separated list
          status INTEGER DEFAULT 0 -- Not sure what this is going to be for yet 
        );

        CREATE TABLE IF NOT EXISTS groups(
          id INTEGER PRIMARY KEY,
          name TEXT NOT NULL,
          description TEXT DEFAULT '',
          status INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS asset_counter(
          asset_id INTEGER DEFAULT 0
        );

        INSERT INTO asset_counter (asset_id) VALUES (0);

        CREATE TABLE IF NOT EXISTS "songs" (
          "name" TEXT,
          "gdrive" TEXT
        );
      """)
    except Exception as e:
      print("Database creation error!")
      print(e)
      
    from app.landing import landing_bp
    app.register_blueprint(landing_bp)

    # Select the desired config object from FLASK_ENV environment variable
    try:
      app.config.from_object(config[config_name])
      config[config_name].init_app(app)
    except Exception as e:
      print('')
      print('An error occurred initalizing the app. Be sure to set the environment')
      print('variables FLASK_ENV=(development|production) and FLASK_APP=application.py')
      print('')
      raise e

    return app
