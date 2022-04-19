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

@app.template_filter('date_to_color')
def date_to_color(date):
    year = date[0:4]
    
    map = {
        '2023': 'LightSkyBlue',
        '2022': 'LightSkyBlue',
        '2021': 'Wheat',
        '2020': 'Gold',
        '2019': 'Tomato',
        '2018': 'Salmon'
    }

    return map.get(year, 'Gainsboro')