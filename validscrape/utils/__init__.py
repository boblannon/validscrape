import datetime

from .data_munge import get_key, set_key, del_key, map_vals
from .file_ops import mkdir_p, translate_dir
from .generic import canonize_url, JSONEncoderPlus
# from .log import set_up_logging

from validictory.validator import SchemaValidator

class DatetimeValidator(SchemaValidator):
    """ add 'datetime' type that verifies that it has a datetime instance """

    def validate_type_datetime(self, x):
        return isinstance(x, (datetime.date, datetime.datetime))
