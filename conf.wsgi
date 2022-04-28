#!/usr/bin/python
import os

# Work around needed to s3.py can access keys in config.py outside of the app context.
os.environ['FLASK_ENV']= 'production'
os.environ['APPLICATION_ROOT'] = 'audio'

from myapp import app as application
