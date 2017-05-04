from BaseController import BaseController
import tornado.ioloop
import tornado.web
import dateutil.parser
import datetime
from dateutil import tz

class ExpiredEvictedController(BaseController):

    def convert_gmt2est(self, gmt):
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()
        utc = datetime.datetime.strptime(gmt, '%Y-%m-%d %H:%M:%S')
        # Tell the datetime object that it's in UTC time zone since
        # datetime objects are 'naive' by default
        utc = utc.replace(tzinfo=from_zone)
        # Convert time zone
        return utc.astimezone(to_zone)

    def get(self):
        server = self.get_argument("server")
        from_date = self.get_argument("from", None)
        to_date = self.get_argument("to", None)

        return_data = dict(data=[],
                           timestamp=datetime.datetime.now().isoformat())

        if not from_date or not to_date:
            end = datetime.datetime.now()
            delta = datetime.timedelta(seconds=60)
            start = end - delta
        else:
            start = self.convert_gmt2est(str(dateutil.parser.parse(from_date))[0:-6])
            end   = self.convert_gmt2est(str(dateutil.parser.parse(to_date))[0:-6])

            # print('from_date:%s %s, to_date:%s %s' % (from_date, start, to_date, end))

        combined_data = []
        # TODO: These variables aren't currently used; should they be removed?
        prev_max=0
        prev_current=0
        counter=0

        expired_evicted_info = self.stats_provider.get_expired_evicted_info(server, start, end)
        inc = round(float(len(expired_evicted_info)) / 375)
        index = 0
        for data in expired_evicted_info:
            index += 1
            if inc <= index:
                index = 0
                combined_data.append([data[0], data[1], data[2]])

        for data in combined_data:
            d = [self.datetime_to_list(data[0]), data[1], data[2]]
            return_data['data'].append(d)

        self.write(return_data)

