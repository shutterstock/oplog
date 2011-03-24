# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

from twisted.internet import defer
from huck import utils
from oplog import api
from oplog import web

class Error(Exception): pass

class FormError(Error):

    def __init__(self, message, field):
        self.field = field
        super(FormError, self).__init__(message)

class Home(web.Handler):

    @web.authenticated
    def get(self):
        self.render('home.html')

class Api(web.Handler):

    def get_error_html(self, status_code, **kwargs):
        if hasattr(self, 'error'):
            code = self.error.code
            message = unicode(self.error)
        else:
            code = api.INTERNAL_ERROR
            message = api.ERRORS.get(code)
        return utils.json.encode({'error': {'code': code, 'message': message}})

    def validate_message(self, message):
        if not isinstance(message, dict):
            raise api.Error(api.INVALID_REQUEST)
        if not isinstance(message.get('method'), basestring):
            raise api.Error(api.INVALID_REQUEST)
        if not isinstance(message.get('params'), dict):
            raise api.Error(api.INVALID_REQUEST)

    @defer.inlineCallbacks
    @web.authenticated
    def post(self):
        container = {}
        user = self.get_current_user()

        try:
            if not user:
                raise api.Error(api.INVALID_REQUEST)
            try:
                container = utils.json.decode(self.request.body)
            except ValueError:
                raise api.Error(api.PARSE_ERROR)
            if isinstance(container, list):
                # Validate all messages before routing
                for message in container:
                    self.validate_message(message)
                for message in container:
                    data = yield api.route(user, self, message)
                    self.write(utils.json.encode(data))
            else:
                self.validate_message(container)
                data = yield api.route(user, self, container)
                self.write(utils.json.encode(data))
            self.finish()
        except api.Error, error:
            self.error = error
            raise web.Error(error.http_code)

class Login(web.Handler):
    """Log user into Oplog."""

    _authentication = None

    def get(self):
        next = self.request.get('next', '/')
        self.render('login.html', next=next, username='', select='username')

    @defer.inlineCallbacks
    def post(self):
        username = self.request.post('username', '')
        password = self.request.post('password', '')
        next = self.request.post('next', '/').strip()

        try:
            if not username:
                raise FormError('Username required', 'username')
            if not password:
                raise FormError('Password required', 'password')

            valid_user = yield self.plugin(self.settings.plugin.authentication).valid(username, password)

            if not valid_user:
                raise FormError('Invalid username or password.', 'password')

            self.set_current_user(username)

            if not next or next.startswith('/login') or next.startswith('/logout'):
                self.redirect('/')
            else:
                self.redirect(next)
        except FormError, error:
            self.set_error(error)
            self.render('login.html', next=next, username=username, select=error.field)

class Logout(web.Handler):
    """Destroy user session."""

    def get(self):
        self.clear_cookie('session')
        self.render('logout.html')

class NotFound(web.Handler):

    def get(self, url):
        raise web.Error(404)

route = [
    (r'/', Home),
    (r'/api', Api),
    (r'/login', Login),
    (r'/logout', Logout),
    (r'(.*)', NotFound),
]
