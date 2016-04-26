# -*- coding: utf-8 -*-
"""
A quick helper script to create access.json files and generate new unique
access secret and tokens for the service. This will aid the devops / container
folks get off the ground quickly.

Oisin Mulvihill
2016-04-25

"""
import sys
import uuid
import json
import codecs
import logging
from optparse import OptionParser

from apiaccesstoken.tokenmanager import Manager


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


def logtoconsolefallback(log):
    # Log to console instead:
    hdlr = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)
    log.propagate = False


def main():
    """
    """
    parser = OptionParser()

    parser.add_option(
        "-u", "--username", action="store", dest="username",
        default='statsbob',
        help=(
            "The username to generate the access file for (default: %default)."
        )
    )

    parser.add_option(
        "--access_json", action="store", dest="access_json",
        default='/data/access.json',
        help=(
            "The path and filename to write the access JSON configuration to "
            "(default: %default)."
        )
    )

    (options, args) = parser.parse_args()

    log = get_log('main')
    logtoconsolefallback(log)

    log.info("generate for username={} to access.json={}".format(
        options.username, options.access_json
    ))

    access_secret = Manager.generate_secret()
    man = Manager(access_secret)
    access_token = man.generate_access_token(identity=options.username)

    access_data = [{
        u'id': u'user_{}'.format(uuid.uuid4()),
        u'username': options.username,
        u"tokens": [
            {
                u"access_token": access_token,
                u"access_secret": access_secret
            }
        ],
    }]

    with codecs.open(options.access_json, "wb", encoding="utf-8") as fd:
        fd.write(json.dumps(access_data, indent=4))

    print("""

The file {} was written successfully for username '{}'. The following
access_token can be used:

{}

    """.format(
        options.access_json,
        options.username,
        access_token,
    ))

    sys.exit(0)
