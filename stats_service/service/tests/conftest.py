# -*- coding: utf-8 -*-
"""
"""
import json
import codecs
import logging
from pkg_resources import resource_string

import pytest
from apiaccesstoken import tokenmanager
from pytest_service_fixtures.io import *
from pytest_service_fixtures.service import *

# imported to get py.test finding the fixture
from stats_service.backend.tests.conftest import *


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


@pytest.fixture
def user_bob():
    """Return the single user entry for 'bob' and his secrent & access token
    pair.

    :returns: A dict

    E.g.::

        {
            "id": "user_00ca4f6190b84f25827239233c4bcbaa",
            "username": "bob",
            "name": "Stats User"
            "tokens": [
                {
                    "access_token": "eyJ..<auto generated>..w==",
                    "access_secret": "b71..<auto generated>..54e"
                }
            ],
        }

    """
    username = 'bob'
    access_secret = tokenmanager.Manager.generate_secret()
    man = tokenmanager.Manager(access_secret)
    access_token = man.generate_access_token(identity=username)

    return {
        "id": "user_00ca4f6190b84f25827239233c4bcbaa",
        "username": "bob",
        "name": "Stats User",
        "tokens": [
            {
                "access_token": access_token,
                "access_secret": access_secret,
            }
        ],
    }


@pytest.fixture
def access_json(tmpdir_factory, user_bob):
    """Create the access.json the test service will use, which contains the
    details for user_bob. This allows testing using auto-generated tokens.
    """
    fn = tmpdir_factory.mktemp('data').join('access.json')

    fn.write(json.dumps(
        [user_bob],
        # aid debugging if by dumping in a more readable way:
        indent=4
    ))

    return fn


class AnalyticsServerRunner(BasePyramidServerRunner):
    """Run the Analytics Pyramid WebApp."""

    def template_config(self):
        """Return the contents of stats_test_cfg.template."""
        return resource_string(__name__, 'test_cfg.ini.template')


@pytest.fixture
def stats_service(request, backend, user_bob, access_json):
    """Pytest fixture to run a test instance of the service.

    """
    log = get_log("server")

    test_server = AnalyticsServerRunner(dict(
        access_json=access_json,
        influxdb_host=backend['host'],
        influxdb_port=backend['port'],
        influxdb_user=backend['user'],
        influxdb_password=backend['password'],
        influxdb_db=backend['db'],
    ))

    # Set up the client side rest api and set it up with the URI of the
    # running test service.
    from stats_client.client.analytics import Analytics
    log.debug("server: setting up REST client API for URI '{}'.".format(
        test_server.URI
    ))

    # Attach to the server object:
    test_server.api = Analytics(dict(
        url=test_server.URI,
        access_token=user_bob['tokens'][0]['access_token'],
        defer=False
    ))

    def teardown():
        """Stop running the test instance."""
        log.debug("teardown: '{}' stopping instance.".format(test_server.URI))
        test_server.stop()
        test_server.cleanup()
        log.debug("teardown: '{}' stop and cleanup called OK.".format(
            test_server.URI
        ))

    request.addfinalizer(teardown)

    log.debug("server: starting instance.")
    test_server.start()

    return test_server
