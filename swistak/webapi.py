# -*- coding: utf8 -*-
import suds
from suds.client import Client
import hashlib
import base64
from functools import wraps

def requires_session(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        if self.hash is None:
            self.get_hash()
        try:
            return f(self, *args, **kwargs)
        except Swistak.ErrorAuthorization:
            self._prepare_session()
            return f(self, *args, **kwargs)

    return wrapped


class Swistak(object):

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




    def __init__(self, login, password, url='http://www.swistak.pl/out/wsdl/wsdl.html?wsdl'):
        self.hash = None
        self.login = login
        self.password = password
        self.url = url
        self.soap_client = Client(self.url)

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

    @requires_session
    def get_my_auctions(self, user_id, offset=0, limit=25):
        request = {
            'hash' : self.hash,
            'offset' : offset,
            'limit' : limit,
            'user_id' : user_id,
        }
        try:
            return self.soap_client.service.get_my_auctions(**request)
        except suds.WebFault, e:
            if e.fault.faultcode == 'ERR_AUTHORIZATION':
                raise Swistak.ErrorAuthorization()
            elif e.fault.faultcode == 'ERR_INVALID_OFFSET':
                raise ValueError('Offset out of range')
            elif e.fault.faultcode == 'ERR_INVALID_LIMIT':
                raise ValueError('Limit out of range')
            elif e.fault.faultcode == 'ERR_USER_NOT_FOUND':
                raise Swistak.ErrorUserNotFound()
            else:
                raise e

    def get_my_auctions_all(self, user_id, limit=25):
        response = self.get_my_auctions(user_id=user_id, offset=0, limit=limit)
        items_count = int(response['total_auctions'])
        items_list = response['auctions']

        for offset in xrange(items_count/limit):
            print offset
            response = self.get_my_auctions(user_id=user_id, offset=offset+1, limit=limit)
            items_list += response['auctions']

        return items_list