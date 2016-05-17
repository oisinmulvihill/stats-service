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


def setup_auth(found_users):
    """
    """
    log = get_log('setup_auth')
    global _USERS, _USERNAME_TO_ID, _SECRET_FOR_ID

    log.info("configuring '{}' user(s).".format(len(found_users)))
    for user in found_users:
        if _USERS is None:
            _USERS = {}

        # create dict based lookup used in identity recovery.
        _USERS[user['id']] = user

        log.debug(
            "loading user id='{}' username='{}'".format(
                user['id'], user['username']
            )
        )
        _USERNAME_TO_ID[user['username']] = user['id']
        log.debug(
            "user '{}' has '{}' token pair(s) to load.".format(
                user['username'], len(user['tokens'])
            )
        )
        if user['tokens'] < 1:
            log.error(
                (
                    "The user '{}' has no token pairs! No access to the "
                    "stats API will be possible for this user!"
                ).format(
                    user['username'], len(user['tokens'])
                )
            )
        for t in user['tokens']:
            _SECRET_FOR_ID[t['access_token']] = t['access_secret']


def init(id_json_file):
    """Set up the users from a JSON file.
    """
    log = get_log('init')

    id_json_file = os.path.abspath(os.path.expanduser(id_json_file))
    if os.path.isfile(id_json_file):
        with codecs.open(id_json_file, 'rb', encoding='utf-8') as fd:
            log.info("recovering JSON data from '{}'".format(id_json_file))
            found_users = json.loads(fd.read())
            setup_auth(found_users)
    else:
        msg = "can't find the file '{}'".format(id_json_file)
        log.error(msg)
        raise OSError(msg)


def init_from_env(config):
    """Set up the users from a JSON file.
    """
    log = get_log('init_from_env')
    found_users = [
        {
            "username": "statsbob",
            "tokens": [
                {
                    "access_token": config['access_token'],
                    "access_secret": config['access_token'],
                }
            ],
            "id": "user_00ca4f6190b84f25827239233c4bcbaa",
            "name": "Stats User"
        }
    ]
    log.debug("using environment secret and access token.")
    setup_auth(found_users)


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
