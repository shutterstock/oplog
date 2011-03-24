# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

import datetime
import json
import os
import txmongo
import validictory
from twisted.internet import defer
from twisted.python import log
from oplog import utils

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
SERVER_ERROR = -32099

ERRORS = {
    PARSE_ERROR:      'Parse error',      # Invalid JSON was received by the server.
    INVALID_REQUEST:  'Invalid Request',  # The JSON sent is not a valid Request object.
    METHOD_NOT_FOUND: 'Method not found', # The method does not exist / is not available.
    INVALID_PARAMS:   'Invalid params',   # Invalid method parameter(s).
    INTERNAL_ERROR:   'Internal error',   # Internal JSON-RPC error.
    SERVER_ERROR:     'Server error',     # Reserved for implementation-defined server-errors.
}

class Error(Exception):

    def __init__(self, code=INTERNAL_ERROR, message=None, http_code=400):
        self.code = code
        self.http_code = http_code
        if not message:
            message = ERRORS.get(code, INTERNAL_ERROR)
        super(Error, self).__init__(message)

class ServerError(Error):

    def __init__(self, message, code=SERVER_ERROR, **kwargs):
        super(ServerError, self).__init__(code=code, message=message, **kwargs)

class Handler(object):

    _schema = {}
    _schema_list = [os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema')]

    def __init__(self, user, settings, db):
        self.user = user
        self.settings = settings
        self.db = db

    def err(self, message, error):
        log.err('%s (%s): %s' % (message, type(error), error))
        raise ServerError(message)

    def load_schema(self, name):
        for root in self._schema_list:
            path = '%s.json' % os.path.join(root, name)
            if os.path.isfile(path):
                try:
                    with open(path) as f:
                        return json.loads(f.read())
                except Exception, error:
                    log.err('Unable to parse schema: %s' % path)
        log.err('No schema found for: %s' % name)

    def validate(self, name, data):
        if not name in self._schema:
            schema = self.load_schema(name)
            if schema:
                self._schema[name] = schema
        else:
            schema = self._schema.get(name)
        # Only validate if we have a schema defined
        if schema:
            try:
                validictory.validate(data, schema, required_by_default=False)
            except ValueError, error:
                log.err('Validation failed because: %s' % error)
                raise Error(INVALID_PARAMS)

    @defer.inlineCallbacks
    def __call__(self, params):
        result = yield self.run(**params)
        try:
            defer.returnValue({'result': result})
        except TypeError, error:
            log.err('Unable to encode result: %s (%s)' % (error, result))
            raise Error(INTERNAL_ERROR)

    @defer.inlineCallbacks
    def run(self, **kwargs):
        raise Error(METHOD_NOT_FOUND)

class EntryHandler(Handler):

    def backup(self, entry):
        return self.db.entry_history.insert({
            'date': datetime.datetime.utcnow(),
            'body': entry,
            'type': self.name,
        })

class EntryDel(EntryHandler):

    name = 'entry.del'

    @defer.inlineCallbacks
    def run(self, **values):
        self.validate(self.name, values)
        try:
            values = utils.mongify.encode(values)

            # Get old value so we can add to history
            entry = yield self.db.entry.find_one(values)

            if not entry:
                raise Error('Entry with id "%s" not found' % values['_id'])

            result = yield self.db.entry.remove(values, safe=True)

            if not result.get('err'):
                yield self.backup(entry)

            defer.returnValue(result)
        except Exception, error:
            self.err('Failed to delete entry', error)

class EntryGet(EntryHandler):

    name = 'entry.get'

    def gen_sort(self, sort):
        if not sort:
            return
        f = ()
        for name, ordering in sort:
            if ordering == -1:
                f += txmongo.filter.DESCENDING(name)
            elif ordering == 1:
                f += txmongo.filter.ASCENDING(name)
        return txmongo.filter.sort(*f) if f else None

    @defer.inlineCallbacks
    def run(self, **values):
        self.validate(self.name, values)
        find = values['find']
        skip = values.get('skip', 0)
        limit = values.get('limit', 20) # Default to 20 records
        sort = values.get('sort', [])
        fields = values.get('fields')
        try:
            sort = self.gen_sort(sort)
            if '_id' in find:
                find['_id'] = txmongo.ObjectId(find['_id'])
            find = utils.mongify.encode(find)
            results = yield self.db.entry.find(spec=find, skip=skip, limit=limit, filter=sort, fields=fields)
            defer.returnValue(utils.mongify.decode(list(results)))
        except Exception, error:
            log.err('Get entry error: %s' % error)
            raise ServerError('Failed to query entries')

class EntryPut(EntryHandler):

    name = 'entry.put'

    @defer.inlineCallbacks
    def run(self, **values):

        def validate(values):
            # Validate entry.put schema
            self.validate(self.name, values)

            # Validate type schema
            if '_type' in values and isinstance(values['_type'], basestring):
                self.validate('entry.type.%s' % values['_type'], values)

        try:
            # Update if we have an _id, this operation is much less efficient
            # than an insert because of the read, write and possible second
            # write hack to get schema validation
            if '_id' in values:
                _id = txmongo.ObjectId(values.pop('_id'))

                # Get old value so we can revert if schema fails or add to
                # history collection
                old_entry = yield self.db.entry.find_one({'_id': _id})

                if not old_entry:
                    raise Error('Entry with id "%s" not found' % _id)

                result = yield self.db.entry.update(
                    {'_id': _id, '_user': self.user},
                    # "clean" encode is relatively naive and probably adds
                    # little security, but attempts to disallow updates to base
                    # fields that start with an underscore
                    utils.mongify.encode(values, clean=True),
                    upsert=False,
                    safe=True,
                )

                # Get updated value so we can validate
                new_entry = yield self.db.entry.find_one({'_id': _id})

                try:
                    validate(utils.mongify.decode(new_entry))
                except ValueError, error:
                    _id = old_entry.pop('_id')
                    yield self.db.entry.update({'_id': _id}, old_entry, upsert=False, safe=True)
                    raise error
                else:
                    yield self.backup(old_entry)
            else:
                # Set default values
                if not '_date' in values:
                    values['_date'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Enforce user
                values['_user'] = self.user

                validate(values)

                result = yield self.db.entry.insert(utils.mongify.encode(values), safe=True)

            defer.returnValue(utils.mongify.decode(result))
        except Error, error:
            raise error
        except Exception, error:
            self.err('Failed to put entry', error)

ROUTE = {
    EntryDel.name: EntryDel,
    EntryGet.name: EntryGet,
    EntryPut.name: EntryPut,
}

def route(user, request, message):
    return ROUTE.get(message['method'], Handler)(user, request.settings, request.mongo)(message['params'])
