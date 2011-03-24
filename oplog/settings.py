# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

from ops import settings

class Settings(settings.Settings):

    class General(settings.Section):
        debug = settings.Boolean(default=False)
        schema = settings.String(default='/etc/oplog/schema')
        profile = settings.String()

    class Plugin(settings.Section):
        authentication = settings.String(default='oplog.plugin.authentication.development')

    class Email(settings.Section):
        host = settings.String(default='mail.example.org')
        port = settings.Integer(default=25)
        from_address = settings.String(default='oplog@example.org')

    class Http(settings.Section):
        url = settings.String(default='https://oplog.example.org')
        interface = settings.String(default='0.0.0.0')
        port = settings.Integer(default=80)
        cookie_secret = settings.String()

    class Ldap(settings.Section):
        uri = settings.String(default='ldaps://ldap.example.org')
        start_tls = settings.Boolean(default=True)
        user_dn_template = settings.String(default='uid=${user},ou=people,dc=example,dc=org')
        # NOTE(ssewell): stubbed out settings I should probably implement
        bind_dn = settings.String(default='')
        bind_password = settings.String(default='')
        user_search = settings.String(default='ou=people,dc=example,dc=org')
        user_filter_attribute = settings.String(default='uid')

    class Mongo(settings.Section):
        host = settings.String(default='localhost')
        port = settings.Integer(default=27017)
        database = settings.String(default='oplog')
        timeout = settings.Integer(default=3)

    class Theme(settings.Section):
        logo = settings.String(default='')
        reset_password = settings.String(default='')
