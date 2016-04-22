# -*- coding: utf-8 -*-
"""
"""
import logging

from pyramid.httpexceptions import HTTPForbidden


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


class UserError(Exception):
    """ A generic user-related error """


class NoUsernameInMatchdictError(UserError):
    """Raised when username wasn't found in the request matchdict."""

# NO DB just hard coded secure token access only.
_NAME_TO_ID = {
    "pncanalytics": "user_00ca4f6190b84f25827239233c4bcbaa",
}

_TOKEN_TO_ID = {
    (
        "eyJleHBpcmVzIjogMTAsICJzYWx0IjogIjFhNDg2NiIsICJpZGVudGl0eSI6ICJwbmNhb"
        "mFseXRpY3MifQOtFroyPKR6UKIXevPytLKhKQ6A02r70swutaZkJMgX3iCPWoUw1VK-BR"
        "81frJLrWajF4pmpqnTSuNhXl7tcpw="
    ): "user_00ca4f6190b84f25827239233c4bcbaa",
}

# The token the client will use for testing and for the moment in production.
API_ACCESS_TOKEN = _TOKEN_TO_ID.keys()[0]

_USERS = {
    "user_00ca4f6190b84f25827239233c4bcbaa": {
        "id": "user_00ca4f6190b84f25827239233c4bcbaa",
        "name": "PNC Analytics",
        "account_type": "device",
        "description": "PicknChoose Analytics User",
        "email": "systems@picknchoose.me",
        "username": "pncanalytics",
        "link": "http://stats.picknchoose.me/",
        "tokens": [
            (
                "eyJleHBpcmVzIjogMTAsICJzYWx0IjogIjFhNDg2NiIsICJpZGVudGl0eSI6I"
                "CJwbmNhbmFseXRpY3MifQOtFroyPKR6UKIXevPytLKhKQ6A02r70swutaZkJM"
                "gX3iCPWoUw1VK-BR81frJLrWajF4pmpqnTSuNhXl7tcpw="
            )
        ],
        "token_map": {
            (
                "eyJleHBpcmVzIjogMTAsICJzYWx0IjogIjFhNDg2NiIsICJpZGVudGl0eSI6I"
                "CJwbmNhbmFseXRpY3MifQOtFroyPKR6UKIXevPytLKhKQ6A02r70swutaZkJM"
                "gX3iCPWoUw1VK-BR81frJLrWajF4pmpqnTSuNhXl7tcpw="
            ): {
                "access_secret": (
                    "b291fe68461788c6bdbfb1646dd377e5a5731bb02980f63659d3321f3"
                    "19723427a877b7eed04f58eec84b243dd6e53cc72d0901ad4bfd7705e"
                    "1f9501e3bf10d5"
                )
            }
        }
    }
}


def user_for_login(request):
    """Recover the logged in user for auth or token access.

    If no user_id/username was recovered from the environment then
    HTTPForbidden will be raised as a login is required.

    If a user is found this will update their status to 'online'. Their
    status will be updated only if they were 'offline'.

    """
    log = get_log("user_for_login")

    identifier = None

    # standard repoze related identity:
    if 'repoze.who.identity' in request.environ:
        identity = request.environ['repoze.who.identity']

        if 'username' in identity:
            identifier = identity['username']

        elif 'repoze.who.userid' in identity:
            identifier = identity['repoze.who.userid']

    # token based identity:
    elif 'pp.api_access.identity' in request.environ:
        identifier = request.environ['pp.api_access.identity']

    else:
        log.debug("No identifier recovered from environment!")

    if not identifier:
        raise HTTPForbidden()

    if _USERS.get(identifier):
        found = _USERS.get(identifier)

    if _NAME_TO_ID.get(identifier):
        found = _USERS.get(_NAME_TO_ID.get(identifier))

    return found


def secret_for_access_token(access_token):
    """Recover the user for the given access_token.

    :param access_token: The access token string to look with.

    :returns: the secret token string or None if nothing was found.

    """
    access_secret = None
    log = get_log('secret_for_access_token')

    userdict = _USERS.get(_TOKEN_TO_ID.get(access_token))
    if userdict:
        #log.debug("user '{}' found for token.".format(userdict['username']))

        if 'token_map' not in userdict:
            log.info(
                "user '{}' has no token_map field. Skipping.".format(
                    userdict['id']
                )
            )

        elif access_token in userdict['token_map']:
            tm = userdict['token_map']
            access_secret = tm[access_token]['access_secret']
            # log.debug(
            #     "secret found for access_token '{}' owner:'{}'" .format(
            #         access_token, userdict['id']
            #     )
            # )

        else:
            log.error(
                "user '{}' access token: no matching token_map entry!".format(
                    userdict['id']
                )
            )

    if not access_secret:
        log.error(
            "No access secret found for access_token '{}'".format(
                access_token
            )
        )

    return access_secret


def api_access_token_middleware(settings, app):
    """Middleware to allow API Access token authentication.

    :param settings: The pyramid settings dict passed into main.

    :param app: The wsgi application we are wrapping.

    """
    log = get_log('api_access_token_middleware')

    from pp.apiaccesstoken.middleware import ValidateAccessToken

    def recover_secret(access_token):
        """This needs to recover the access_secret for the given access_token.

        :returns: The access_secret or None if nothing was found.

        """
        partial_tk = "{}..<hidden>..{}".format(
            access_token[:4], access_token[-4:]
        )
        log.debug(
            "recover_secret: access_token {}".format(partial_tk)
        )
        return secret_for_access_token(access_token)

    log.info("API token lookup initialised and ready to roll.")

    return ValidateAccessToken(app, recover_secret=recover_secret)
