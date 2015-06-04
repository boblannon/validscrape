import json
import pytz
import datetime
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit, SplitResult


class JSONEncoderPlus(json.JSONEncoder):
    """
    JSONEncoder that encodes datetime objects as Unix timestamps.
    """
    def default(self, obj, **kwargs):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            if obj.tzinfo is None:
                raise TypeError(
                    "date '%s' is not fully timezone qualified." % (obj))
            obj = obj.astimezone(pytz.UTC)
            return "{}".format(obj.isoformat())
        return super(JSONEncoderPlus, self).default(obj, **kwargs)


def canonize_url(url):
    split_url = urlsplit(url)

    canonical_query = urlencode(sorted(parse_qsl(split_url.query)))
    return urlunsplit(SplitResult(scheme=split_url.scheme,
                                  netloc=split_url.netloc,
                                  path=split_url.path,
                                  query=canonical_query,
                                  fragment=split_url.fragment))
