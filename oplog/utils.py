# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

import re
import txmongo
from datetime import datetime

OBJECT_ID = re.compile(r'^[a-f0-9]{24}$')

class mongify:

    @staticmethod
    def _basestring_encode(value, clean=False):
        # TODO(ssewell): are these bad assumptions, maybe extend schema and use
        # that for special types
        if OBJECT_ID.match(value):
            return txmongo.ObjectId(value)
        try:
            return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            pass
        return value

    @staticmethod
    def _datetime_decode(value):
        return value.strftime('%Y-%m-%dT%H:%M:%SZ')

    @staticmethod
    def _objectid_decode(value):
        return str(value)

    @staticmethod
    def _dict_encode(value, clean=False):
        return dict(
            [(mongify.encode(n), mongify.encode(v)) \
                for n, v \
                in value.items() \
                if not clean or n.strip() not in ('_id', '_user')])

    @staticmethod
    def _dict_decode(value):
        return dict([(mongify.decode(n), mongify.decode(v)) for n, v in value.items()])

    @staticmethod
    def _list_encode(value, clean=False):
        return [mongify.encode(value, clean=clean) for v in value]

    @staticmethod
    def _list_decode(value):
        return map(mongify.decode, value)

    @staticmethod
    def encode(value, clean=False):
        if isinstance(value, basestring):
            return mongify._basestring_encode(value, clean=clean)
        elif isinstance(value, dict):
            return mongify._dict_encode(value, clean=clean)
        elif isinstance(value, (list, tuple)):
            return mongify._list_encode(value, clean=clean)
        else:
            return value

    @staticmethod
    def decode(value):
        if isinstance(value, datetime):
            return mongify._datetime_decode(value)
        elif isinstance(value, txmongo.ObjectId):
            return mongify._objectid_decode(value)
        elif isinstance(value, dict):
            return mongify._dict_decode(value)
        elif isinstance(value, (list, tuple)):
            return mongify._list_decode(value)
        else:
            return value
