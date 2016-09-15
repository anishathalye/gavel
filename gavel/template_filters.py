from gavel import app
from humanize import naturaltime

@app.template_filter('utcdatetime_local')
def _jinja2_filter_datetime_local(datetime):
    if datetime is None:
        return 'None'
    return naturaltime(datetime)

@app.template_filter('utcdatetime_epoch')
def _jinja2_filter_datetime_epoch(datetime):
    if datetime is None:
        return 0
    return datetime.strftime('%s')
