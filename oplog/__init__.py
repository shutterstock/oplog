# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

import ConfigParser
import os
from ops import exceptions
from ops import utils as ops_utils
from twisted import plugin
from twisted.application import service
from twisted.internet import reactor
from twisted.python import log
from twisted.python import usage
from txmongo import lazyMongoConnectionPool
from zope.interface import implements
from oplog import handler
from oplog import settings
from oplog import web

class Service(service.Service):

    def __init__(self, settings):
        self.settings = settings
        self.http_factory = web.Application(handler.route, settings)

    def startService(self):
        service.Service.startService(self)

        self.http_factory.mongo = lazyMongoConnectionPool(
            host=self.settings.mongo.host,
            port=self.settings.mongo.port,
        )

        reactor.listenTCP(
            port=self.settings.http.port,
            factory=self.http_factory,
            interface=self.settings.http.interface,
        )

    def stopService(self):
        service.Service.stopService(self)

class Options(usage.Options):

    optParameters = [ 
        ['config-file', 'c', '/etc/oplog/main.conf', None, unicode],
    ]

class ServiceMaker(object):
    implements(service.IServiceMaker, plugin.IPlugin)
    tapname = 'oplog'
    description = 'An operations log'
    options = Options

    def makeService(self, options):
        s = settings.Settings(self.tapname, optparse=False)
        try:
            p = s.parse(config_file=options['config-file'])
            # Check and parse profile configuration file
            if not os.path.isfile(p.general.profile):
                raise exceptions.Error('invalid profile configuration path')
            config = ConfigParser.ConfigParser()
            if not config.read([p.general.profile]):
                raise exceptions.Error('unable to parse profile configuration file')
            def profile(name, key):
                return config.has_section(name) and config.has_option(name, 'key') and config.get(name, 'key') == key
            p.general.profile = profile
            return Service(p)
        except (ConfigParser.Error, exceptions.Error), error:
            ops_utils.exit(1, error)
