# -*- coding: utf-8 -*-
"""
"""
import logging

from pytest_service_fixtures.io import *
from pytest_service_fixtures.service import *


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


@pytest.fixture
def backend(request, influxdb):
    """Set up backend db with influxdb fixture and return config dict for it.
    """
    log = get_log('backend')

    config = dict(
        db=influxdb.db,
        port=influxdb.port,
        host=influxdb.host,
        user=influxdb.user,
        password=influxdb.password,
    )

    # Set up connection to aid testing:
    from stats_service.backend import db

    db.DB.init(config)
    db.DB.create_database()
    log.info('database ready for testing "{}"'.format(influxdb.db))

    # def db_teardown(x=None):
    #     log.warn('teardown database for testing "{}"'.format(dbconn.db))
    #     db.DB.drop_database()

    # request.addfinalizer(db_teardown)

    return config
