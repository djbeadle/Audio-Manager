import urllib.parse
from myapp import app


@app.template_filter('unquote')
def unquote(value):
    """
    Prettyify filenames for human consumption
    """
    return urllib.parse.unquote_plus(value)

@app.template_filter('file_id')
def file_id(value):
    return value.split('_')[0]
