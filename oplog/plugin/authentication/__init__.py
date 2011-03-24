# Copyright (c) 2011, Shutterstock Images LLC.
# All rights reserved.
#
# This file is subject to the MIT License (see the LICENSE file).

class Base(object):

    def __init__(self, settings, *args, **kwargs):
        self.settings = settings

    def valid(self, username, password):
        raise NotImplementedError('Authentication valid check not implemented.')
