from datetime import datetime
import locale
import re
from functools import reduce

REPLACE_MAP = {u'&#160;': u'',
               u'\xa0': u'',
               u'\u200b': u'',
               u'&nbsp;': u''}

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

DATE_FORMATS = ['%m/%d/%Y',
                '%m/%d/%Y %I:%M:%S %p',
                '%m/%d/%y',
                '%Y/%m/%d',
                '%m-%d-%Y',
                '%m-%d-%y']

LEAP_DAY_CHECKS = [
    re.compile(r'^(?P<year>(19|20)[0-9]{2})'
               r'[/-]'
               r'(?P<month>0?2)'
               r'[/-]'
               r'(?P<day>29)$'),

    re.compile(r'^(?P<month>0?2)'
               r'[/-]'
               r'(?P<day>29)'
               r'[/-]'
               r'(?P<year>(19|20)?[0-9]{2})$')
]


def get_key(my_dict, key):
    return reduce(dict.get, key.split("."), my_dict)


def set_key(my_dict, key, value):
    keys = key.split(".")
    my_dict = reduce(dict.get, keys[:-1], my_dict)
    my_dict[keys[-1]] = value


def del_key(my_dict, key):
    keys = key.split(".")
    my_dict = reduce(dict.get, keys[:-1], my_dict)
    del my_dict[keys[-1]]


def map_vals(copy_map, original, template={}):
    _original = original.copy()
    _transformed = template
    for orig_loc, trans_loc in copy_map:
        val = get_key(_original, orig_loc)
        set_key(_transformed, trans_loc, val)
    return _transformed


def checkbox_boolean(e):
    return 'checked' in e.attrib


def clean_text(e):
    s = e.text or ''
    s = s.strip()
    for p, r in REPLACE_MAP.items():
        s = s.replace(p, r)
    return s


def parse_datetime(e):
    s = clean_text(e)
    parsed = None
    if s:
        f = 0
        for f in DATE_FORMATS:
            try:
                parsed = datetime.strptime(s, f).isoformat(sep=' ')
            except ValueError:
                continue
            else:
                return parsed
        else:
            return s
    else:
        return None


def parse_date(e):
    s = clean_text(e)
    parsed = None
    if s:
        f = 0
        for f in DATE_FORMATS:
            try:
                parsed = datetime.strptime(s, f).strftime('%Y-%m-%d')
            except ValueError:
                continue
            else:
                return parsed
        else:
            for p in LEAP_DAY_CHECKS:
                m = p.match(s)
                if m is not None:
                    groups = m.groupdict()
                    adjusted = datetime(year=int(groups['year']),
                                        month=int(groups['month']),
                                        day=28)
                    return adjusted.strftime('%Y-%m-%d')
            return s
    else:
        return None


def tail_text(e):
    s = e.tail
    for p, r in REPLACE_MAP.iteritems():
        s = s.replace(p, r)
    return s.strip()


def parse_decimal(e):
    s = clean_text(e)
    if s:
        return locale.atof(s)
    else:
        return None


def parse_int(e):
    s = clean_text(e)
    if s:
        return int(s)
    else:
        return None


def parse_percent(e):
    s = clean_text(e).replace('%', '')
    if s:
        return float(s) / 100.0
    else:
        return None


def split_keep_rightmost(e):
    s = clean_text(e)
    split_text = s.split(' ')
    if len(split_text) > 1:
        return split_text[-1]
    else:
        return None


def split_drop_leftmost(e):
    s = clean_text(e)
    split_text = s.split(' ')
    if len(split_text) > 1:
        return ' '.join(split_text[1:])
    else:
        return None


def parse_array(array, children):
    out = []
    for element in array:
        record = {}
        for child in children:
            _parser = child['parser']
            _field = child['field']
            _path = child['path']
            _child_sel = element.xpath(_path)
            if child.get('children', False):
                record[_field] = _parser(_child_sel, child['children'])
            else:
                record[_field] = _parser(_child_sel[0])
        out.append(record)
    return out


def parse_even_odd(array, children):
    for even, odd in [(array[i], array[i + 1])
                      for i in range(0, len(array), 2)]:
        record = {}
        for child in children['even']:
            _parser = child['parser']
            _field = child['field']
            _path = child['path']
            _child_node = even.xpath(_path)[0]
            record[_field] = _parser(_child_node)
        for child in children['odd']:
            _parser = child['parser']
            _field = child['field']
            _path = child['path']
            _child_node = odd.xpath(_path)[0]
            record[_field] = _parser(_child_node)
        yield record
