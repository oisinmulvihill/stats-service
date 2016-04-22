# -*- coding: utf-8 -*-
"""
"""
import os
import json
import codecs
import logging

from apiaccesstoken.middleware import UserAccess
from apiaccesstoken.exceptions import HTTPForbidden
from apiaccesstoken.middleware import TokenMiddleware


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


# set up by init(...)
_USERS = None
_USERNAME_TO_ID = {}
_SECRET_FOR_ID = {}


def init(id_json_file):
    """Set up the users from a JSON file.
    """
    log = get_log('init')
    global _USERS, _USERNAME_TO_ID, _SECRET_FOR_ID

    id_json_file = os.path.abspath(os.path.expanduser(id_json_file))
    if os.path.isfile(id_json_file):
        with codecs.open(id_json_file, 'rb', encoding='utf-8') as fd:
            log.info("recovering JSON data from '{}'".format(id_json_file))
            _USERS = json.loads(fd.read())

        log.info("configuring '{}' user(s) from '{}'".format(
            len(_USERS), id_json_file
        ))
        for user in _USERS:
            _USERNAME_TO_ID[user['username']] = user['id']
            for t in user['tokens']:
                _SECRET_FOR_ID[t['access_token']] = t['access_secret']

    else:
        msg = "can't find the file '{}'".format(id_json_file)
        log.error(msg)
        raise OSError(msg)


class TokenMW(TokenMiddleware):

    def recover_secret(self, access_token):
        """Recover the secret token for the given access_token.

        The end-developer must override to provide the functionality needed.

        :param access_token: The access token string to search for with.

        :returns: the secret token string or None if nothing was found.

        """
        return _SECRET_FOR_ID.get(access_token)


class Access(UserAccess):

    @classmethod
    def recover_user(cls, identifier):
        log = get_log('Access.recover_user')

        log.debug("recover_user by identifier '{}'".format(identifier))
        found = None

        if _USERS is None:
            msg = "init(identity json file) has not been called!"
            log.error(msg)
            raise ValueError(msg)

        if _USERS.get(identifier):
            found = _USERS.get(identifier)

        if _USERNAME_TO_ID.get(identifier):
            found = _USERS.get(_USERNAME_TO_ID.get(identifier))

        # helpful debug
        print("For identifier '{}' I found {}".format(
            identifier,
            "Nothing :(" if found is None else found
        ))

        if found is None:
            raise HTTPForbidden()

        return found
