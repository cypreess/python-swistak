# -*- coding: utf8 -*-
import logging
import suds
from suds.client import Client
from functools import wraps

logger = logging.getLogger('swistak_webapi')


def requires_session(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        if not self._is_session():
            self._prepare_session()
        try:
            return f(self, *args, **kwargs)
        except Swistak.ErrorAuthorization:
            self._prepare_session()
            return f(self, *args, **kwargs)
    return wrapped


def wrap_api_error(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except suds.WebFault, e:
            logger.error("Error in %s, key=[%s]\n%s\n%s\n\n" % (f.__name__, self.login, e.fault, e.document))
            if e.fault.faultcode == 'ERR_USER_PASSWD':
                raise Swistak.ErrorUserPassword()
            elif e.fault.faultcode == 'ERR_USER_BLOCKED':
                raise Swistak.ErrorUserBlocked()
            elif e.fault.faultcode == 'ERR_USER_BLOCKED_ONE_HOUR':
                raise Swistak.ErrorUserTemporarilyBlocked()
            elif e.fault.faultcode == 'ERR_INVALID_IDS':
                raise Swistak.ErrorInvalidIds()
            elif e.fault.faultcode == 'ERR_TOO_MANY_IDS':
                raise Swistak.ErrorTooManyIds()
            elif e.fault.faultcode == 'ERR_AUTHORIZATION':
                raise Swistak.ErrorAuthorization()
            elif e.fault.faultcode == 'ERR_INVALID_OFFSET':
                raise ValueError('Offset out of range')
            elif e.fault.faultcode == 'ERR_INVALID_LIMIT':
                raise ValueError('Limit out of range')
            elif e.fault.faultcode == 'ERR_USER_NOT_FOUND':
                raise Swistak.ErrorUserNotFound()
            else:
                raise e

    return wrapped



class Swistak(object):

    _AUCTIONS_LIMIT = 100

    class ErrorUserPassword(Exception):
        pass

    class ErrorUserBlocked(Exception):
        pass

    class ErrorUserTemporarilyBlocked(Exception):
        pass

    class ErrorUserNotFound(Exception):
        pass

    class ErrorAuthorization(Exception):
        pass

    class ErrorInvalidIds(Exception):
        pass

    class ErrorTooManyIds(Exception):
        pass




    def __init__(self, login, password, url='http://www.swistak.pl/out/wsdl/wsdl.html?wsdl'):
        self.hash = None
        self.login = login
        self.password = password
        self.url = url
        self.soap_client = Client(self.url)

    def _is_session(self):
        return not self.hash is None

    def _prepare_session(self):
        self.get_hash()

    def get_hash(self):
        request = {
            'login': self.login,
            'pass': self.password,
        }
        try:
            self.hash = self.soap_client.service.get_hash(**request)
            return self.hash
        except suds.WebFault, e:
            if e.fault.faultcode == 'ERR_USER_PASSWD':
                raise Swistak.ErrorUserPassword()
            elif e.fault.faultcode == 'ERR_USER_BLOCKED':
                raise Swistak.ErrorUserBlocked()
            elif e.fault.faultcode == 'ERR_USER_BLOCKED_ONE_HOUR':
                raise Swistak.ErrorUserTemporarilyBlocked()
            else:
                raise e

    def get_id_by_login(self, login):
        request = {
            'login': login,
        }
        try:
            return self.soap_client.service.get_id_by_login(**request)
        except suds.WebFault, e:
            if e.fault.faultcode == 'ERR_USER_NOT_FOUND':
                raise Swistak.ErrorUserNotFound()
            else:
                raise e

    @wrap_api_error
    @requires_session
    def get_my_auctions(self, user_id, offset=0, limit=100):
        request = {
            'hash' : self.hash,
            'offset' : offset,
            'limit' : limit,
            'user_id' : user_id,
        }
        return self.soap_client.service.get_my_auctions(**request)


    def get_my_auctions_all(self, user_id, limit=100):
        response = self.get_my_auctions(user_id=user_id, offset=0, limit=limit)
        items_count = int(response['total_auctions'])
        items_list = response['auctions']

        for offset in xrange(items_count/limit):
            response = self.get_my_auctions(user_id=user_id, offset=offset+1, limit=limit)
            items_list += response['auctions']

        return items_list

    @wrap_api_error
    @requires_session
    def get_auctions(self, ids):
        request = {
            'hash' : self.hash,
            'ids' : ids,
            }
        return self.soap_client.service.get_auctions(**request)