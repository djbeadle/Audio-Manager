import urllib.parse
from myapp import app


@app.template_filter('unquote')
def unquote(value):
    """
    Prettyify filenames for human consumption
    """
    return urllib.parse.unquote_plus(value)
