from gavel import app
from humanize import naturaltime
from datetime import timedelta

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

@app.template_filter('timedelta_legible')
def _jinja2_filter_timedelta_legible(tdelta):
	print("{}, {}".format(type(tdelta), tdelta))
	if type(tdelta) == timedelta:
		days = tdelta.days
		tot_seconds = tdelta.seconds

		tot_minutes, seconds = divmod(tot_seconds, 60)
		hours, minutes = divmod(tot_minutes, 60)

		plural = lambda count: "" if count == 1 else "s"

		time_parts = [days, hours, minutes, seconds]
		day_str = "" if days == 0 else "{} day{}, ".format(days, plural(days))
		hour_str = "" if days + hours == 0 else "{} hour{}, ".format(hours, plural(hours))
		minutes_str = "" if days + hours + minutes  == 0 else "{} minute{} and ".format(minutes, plural(minutes))
		return day_str + hour_str + minutes_str +  "{} second{}".format(seconds, plural(seconds)) 
	else:
		return ""