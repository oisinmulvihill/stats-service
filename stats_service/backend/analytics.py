# -*- coding: utf-8 -*-
"""
"""
import os
import uuid
import time
import logging
import datetime

from stats_service.backend import db

from influxdb.client import InfluxDBClientError


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


def table_name():
    """Get the environment variable TABLE_NAME or 'analytics' by default."""
    return os.environ.get('TABLE_NAME', 'analytics')


# http://stackoverflow.com/questions/6999726/
#   python-converting-datetime-to-millis-since-epoch-unix-time

def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def unix_time_millis(dt):
    return unix_time(dt) * 1000.0


def eid():
    i = 'entry_{}'.format(uuid.uuid4())
    return i.replace('-', '')


def influxdb_format(d, now=None):
    """Convert to format I can POST to influxdb.

    This is based on the format described here:

     * http://influxdb.com/docs/v0.8/api/ \
            reading_and_writing_data.html#writing-data-through-http

    :param d: A dictionary with no nested structures.

    :param now: A datetime to use for timestamp.

    If this is not given then the current time will be used. This is converted
    into a milliseconds epoch time and used as the "time" column added to aid
    ordering.

    :returns: (event_id, [write points])

    """
    if 'now' not in d:
        if now:
            d['now'] = unix_time_millis(now)
        else:
            d['now'] = time.time()

    if now:
        d['now'] = unix_time_millis(now)

    if 'event_id' not in d:
        d['event_id'] = eid()

    event_id = d['event_id']

    fields = d.keys()
    fields.sort()

    returned = [
        {
            "measurement": table_name(),
            "tags": d,
            "fields": d,
        }
    ]

    return (event_id, returned)


def find(**kwargs):
    """A rough-and-ready search by key-values or just return all items.

    This is used mainly for testing purposes.

    """
    log = get_log("find")

    conn = db.DB.conn()
    table = table_name()
    try:
        where = ""
        for key, value in kwargs.items():
            where = "{} = '{}' ".format(key, value)

        if where:
            sql = r"SELECT * FROM {} WHERE {}".format(table, where)

        else:
            sql = r"SELECT * FROM {}".format(table)

        log.debug("sql: {}".format(sql))
        results = [i for i in conn.query(sql)]
        if results:
            results = results[0]

    except InfluxDBClientError as e:
        log.warn("column or table not found: {}".format(e))
        results = 0

    return results


def count():
    """The total amount of analytic events stored.

    This is used mainly for testing purposes.

    """
    log = get_log("count")

    conn = db.DB.conn()
    try:
        sql = r"SELECT * FROM {}".format(table_name())
        results = [i for i in conn.query(sql)]
        if results:
            results = len(results[0])
        else:
            results = 0

    except InfluxDBClientError as e:
        log.warn("column or table not found: {}".format(e))
        results = 0

    return results


def log(data):
    """Log an analytic event.

    :param data: This is dictionary that must contain at least uid and event.

    The 'uid' is the unique id used to tie analytic events together as part
    of the same session. It can be empty but the field is required.

    The 'event' is the the end user classification of the event. For example
    'pnc.user.log'.

    The 'time' epoch timestamp will be added automatically to the data. There
    will also be an 'entry-<UUID4>' id given to the specific event.

    """
    assert 'uid' in data
    assert 'event' in data

    log = get_log("log")

    conn = db.DB.conn()

    log.debug("formatting for influx: {}".format(data))
    (event_id, idbfmt) = influxdb_format(data)

    log.debug("writing points to influx:{}".format(idbfmt))
    try:
        conn.write_points(idbfmt)

    except InfluxDBClientError, e:
        if e.code == 404:
            log.warn(
                "Database {} not present {}. Attempting to create.".format(
                    conn._database, e
                )
            )
            conn.create_database(conn._database)
            log.warn("Retrying write to new DB '{}'".format(conn._database))
            conn.write_points(idbfmt)

    return event_id


def get(event_id):
    """Recover a specific anayltics event based on its unique id.

    :param event_id: The unique analytic event id string.

    Not sure this is the best way but I'm only using this in testing at
    the moment.

    :returns: A dict of the found analytic event.

    If the event_id was not found then ValueError will be raised.

    """
    log = get_log("get")

    assert event_id

    conn = db.DB.conn()

    sql = r"SELECT * FROM {} WHERE event_id = '{}'".format(
        table_name(),
        event_id,
    )
    log.debug("Looking for analytic event '{}'".format(event_id))

    found = None
    for i in conn.query(sql):
        found = i
        break

    if found is None:
        raise ValueError("Nothing found for event_id '{}'".format(event_id))

    data = found[0]
    log.debug("found for event_id '{}': {}".format(event_id, data))

    return data
