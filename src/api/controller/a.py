from datetime import datetime
from dateutil import tz

# METHOD 1: Hardcode zones:
# from_zone = tz.gettz('UTC')
# to_zone = tz.gettz('America/New_York')

# METHOD 2: Auto-detect zones:
from_zone = tz.tzutc()
to_zone = tz.tzlocal()

# utc = datetime.utcnow()
utc = datetime.strptime('2011-01-21 02:37:21', '%Y-%m-%d %H:%M:%S')
print utc

# Tell the datetime object that it's in UTC time zone since
# datetime objects are 'naive' by default
utc = utc.replace(tzinfo=from_zone)
print utc

# Convert time zone
central = utc.astimezone(to_zone)
print central
