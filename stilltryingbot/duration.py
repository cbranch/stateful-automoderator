import re
from dateutil.relativedelta import *

duration_re = re.compile(r'((?P<months>\d+?) ?months?)? *((?P<weeks>\d+?) ?weeks?)? *((?P<days>\d+?) ?days?)?')
def parse_duration(duration):
    parts = duration_re.match(duration)
    if not parts:
        return
    parts = parts.groupdict()
    return relativedelta(months=int(parts['months'] or '0'), weeks=int(parts['weeks'] or '0'), days=int(parts['days'] or '0'))

