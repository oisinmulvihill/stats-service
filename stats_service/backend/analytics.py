# -*- coding: utf-8 -*-
"""
"""
import logging

from stats_service.backend import db

from influxdb.client import InfluxDBClientError


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


def find(measurement, **kwargs):
    """A rough-and-ready search by key-values or just return all items.

    This is used mainly for testing purposes.

    """
    log = get_log("find")

    conn = db.DB.conn()
    try:
        where = ""
        for key, value in kwargs.items():
            where = "{} = '{}' ".format(key, value)

        if where:
            sql = r"SELECT * FROM {} WHERE {}".format(measurement, where)

        else:
            sql = r"SELECT * FROM {}".format(measurement)

        log.debug("sql: {}".format(sql))
        results = [i for i in conn.query(sql)]
        if results:
            results = results[0]

    except InfluxDBClientError as e:
        log.warn("column or measurement not found: {}".format(e))
        results = 0

    return results


def count(measurement):
    """The total amount of entries stored in a measurement.

    This is used mainly for testing purposes.

    """
    log = get_log("count")

    conn = db.DB.conn()
    try:
        sql = r"SELECT * FROM {}".format(measurement)
        results = [i for i in conn.query(sql)]
        if results:
            results = len(results[0])
        else:
            results = 0

    except InfluxDBClientError as e:
        log.warn("column or table not found: {}".format(e))
        results = 0

    return results


def log(points):
    """Log an analytic event.

    :param points: A list of (measurement, tags, fields) to be stored.

    E.g.::

        [
            {
                "measurement": measurement1,
                "tags": tags1,
                "fields": fields1,
            },
            {
                "measurement": measurement2,
                "tags": tags2,
                "fields": fields2,
            },
            :
            etc
        ]

    """
    log = get_log("log")

    conn = db.DB.conn()

    ifdb_points = []
    for pt in points:
        # Don't just write anything, pull out only the fields we need.
        ifdb_points.append(
            {
                "measurement": pt['measurement'],
                "tags": pt['tags'],
                "fields": pt['fields'],
            }
        )

    try:
        conn.write_points(ifdb_points)

    except InfluxDBClientError, e:
        if e.code == 404:
            log.warn(
                "Database {} not present {}. Attempting to create.".format(
                    conn._database, e
                )
            )
            conn.create_database(conn._database)
            log.warn("Retrying write to new DB '{}'".format(conn._database))
            conn.write_points(ifdb_points)
