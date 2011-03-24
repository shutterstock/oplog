# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

import httplib
import os
import sys
from twisted.python import log
from huck import mail
from huck import web
from huck.web import HTTPError as Error
from huck.web import authenticated
from oplog import api

class Handler(web.RequestHandler):

    _plugins = {}
    settings = None

    @property
    def mongo(self):
        return self.application.mongo[self.settings.mongo.database]

    def prepare(self):
        self._message_type = ''
        self._message_text = ''
        cookie = ''
        try:
            cookie = self.get_secure_cookie('message')
            if cookie:
                self._message_type, self._message_text = cookie.split(':', 1)
        except Exception, error:
            log.err('Failed to parse message cookie: %s' % error)
        finally:
            if cookie:
                self.clear_cookie('message')

    def plugin(self, name):
        if name not in self._plugins:
            __import__(name) 
            self._plugins[name] = sys.modules[name].register(self.settings)
        return self._plugins[name]

    def _set_message(self, ntype, message, cookie=False):
        if cookie:
            self.set_secure_cookie('message', '%s:%s' % (ntype, message), expires_days=1)
        else:
            self._message_type = unicode(ntype)
            self._message_text = unicode(message)

    def set_error(self, message, cookie=False):
        self._set_message('error', message, cookie)

    def set_notice(self, message, cookie=False):
        self._set_message('notice', message, cookie)

    def set_info(self, message, cookie=False):
        self._set_message('info', message, cookie)

    def set_success(self, message, cookie=False):
        self._set_message('success', message, cookie)

    def render(self, template, **kwargs):
        kwargs['message_text'] = self._message_text
        kwargs['message_type'] = self._message_type
        kwargs['settings'] = self.settings
        super(Handler, self).render(template, **kwargs)

    def get_error_html(self, status_code, **kwargs):
        kwargs['error_code'] = status_code
        kwargs['error_text'] = httplib.responses[status_code]
        kwargs['message_text'] = ''
        kwargs['message_type'] = ''
        kwargs['settings'] = self.settings
        return self.render_string('error.html', **kwargs)

    def get_current_user(self):
        username = self.get_secure_cookie('session')
        if username:
            return username
        else:
            app = self.request.get('app', None)
            key = self.request.get('key', None)
            if app and key and self.settings.general.profile(app, key):
                return '[%s]' % app
            else:
                return None

    def set_current_user(self, username):
        if username:
            self.set_cookie('user', username, expires_days=1) # Only used by javascript
            self.set_secure_cookie('session', username, expires_days=1)

    def email(self, to, subject, message):
        mailconf = {
            'host': self.settings.email.host,
            'port': self.settings.email.port,
            'tls': False,
        }
        message = mail.Message(self.settings.email.from_address, to, subject, message)
        return mail.sendmail(mailconf, message)

class Application(web.Application):

    mongo = None

    def __init__(self, route, settings):
        root_path = os.path.dirname(os.path.realpath(__file__))

        setup = {
            'cookie_secret': settings.http.cookie_secret,
            'debug': settings.general.debug,
            'login_url': '/login',
            'root_path': root_path,
            'static_path': os.path.join(root_path, 'static'),
            'template_path': os.path.join(root_path, 'templates'),
        }

        route.append((r'/static/(.*)', web.StaticFileHandler, {'path': setup['template_path']}))

        Handler.settings = settings
        api.Handler._schema_list.append(settings.general.schema)

        web.Application.__init__(self, route, **setup)
