# -*- coding: utf-8 -*-
"""
"""
import logging

from influxdb import InfluxDBClient


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


class DB(object):
    """A namespace around InfluxDB client creation.
    """
    _SETTINGS = dict(
        host="localhost",
        port=8086,
        user='user',
        password='pass',
        db='testdb',
    )

    @classmethod
    def init(cls, config={}, prefix=''):
        """Set the configuration used to create influxdb clients.

        :param config: a dict.

        This has the following defaults::

            dict(
                host="localhost",
                port=8086,
                user='user',
                password='pass',
                db='testdb',
            )

        """
        log = get_log("DB.init")

        for key in cls._SETTINGS:
            k = "{}{}".format(prefix, key)
            v = config.get(k, cls._SETTINGS[key])
            cls._SETTINGS[key] = v

        s = cls._SETTINGS.copy()
        s['password'] = "<hidden>"
        log.debug("DB configuration: {}".format(s))

    @classmethod
    def conn(cls):
        """Return a InfluxDBClient(...) instances based on init() calls set up.
        """
        return InfluxDBClient(
            cls._SETTINGS['host'],
            int(cls._SETTINGS['port']),
            cls._SETTINGS['user'],
            cls._SETTINGS['password'],
            cls._SETTINGS['db']
        )

    @classmethod
    def drop_database(cls):
        """Used for testing to drop
        """
        log = get_log("DB.drop_database")
        conn = cls.conn()
        log.warn("Dropping database '{}'".format(cls._SETTINGS['db']))
        conn.drop_database(cls._SETTINGS['db'])
        log.info("database '{}' dropped OK.".format(cls._SETTINGS['db']))

    @classmethod
    def create_database(cls):
        """Used for testing to drop
        """
        log = get_log("DB.create_database")
        conn = cls.conn()
        log.info("Creating database '{}'".format(cls._SETTINGS['db']))
        conn.create_database(cls._SETTINGS['db'])
        log.info("database '{}' created OK.".format(cls._SETTINGS['db']))
