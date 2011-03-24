# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

import string
from twisted.internet import defer
from twisted.python import log
import txldap
from oplog.plugin import authentication

class Error(Exception): pass

class Authentication(authentication.Base):

    def __init__(self, *args, **kwargs):
        super(Authentication, self).__init__(*args, **kwargs)
        self.template = string.Template(self.settings.ldap.user_dn_template)

    @defer.inlineCallbacks
    def valid(self, username, password):
        ldap = txldap.Connection(self.settings.ldap.uri)
        if self.settings.ldap.start_tls and not self.settings.ldap.uri.startswith('ldaps://'):
            yield ldap.start_tls()
        try:
            # NOTE(ssewell): we should probably support search and bind
            user_dn = self.template.safe_substitute({'user': txldap.dn.escape_dn_chars(username)})
            yield ldap.bind(user_dn, password)
            defer.returnValue(True)
        except txldap.INVALID_CREDENTIALS:
            defer.returnValue(False)
        except txldap.LDAPError, error:
            log.err('Failed to bind: %s' % error)
        finally:
            try:
                ldap.unbind()
            except Exception, error:
                log.err('Failed to unbind: %s' % error)

def register(settings, *args, **kwargs):
    return Authentication(settings)
