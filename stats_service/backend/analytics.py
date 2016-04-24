# -*- coding: utf-8 -*-
"""
"""
import uuid
import time
import logging
import datetime

from stats_service.backend import db

from influxdb.client import InfluxDBClientError


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


TABLE_NAME = "analytics"


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


def influxdb_format(d, now=None, entry_id=None):
    """Convert to format I can POST to influxdb.

    This is based on the format described here:

     * http://influxdb.com/docs/v0.8/api/ \
            reading_and_writing_data.html#writing-data-through-http

    :param d: A dictionary with no nested structures.

    :param now: A datetime to use for timestamp.

    If this is not given then the current time will be used. This is converted
    into a milliseconds epoch time and used as the "time" column added to aid
    ordering.

    :returns: (entry_id, [write points])

    """
    fields = d.keys()
    fields.sort()

    if not now:
        now = time.time()
    else:
        now = unix_time_millis(now)

    if not entry_id:
        entry_id = eid()

    returned = [
        {
            "measurement": TABLE_NAME,
            "tags": d,
            "fields": d,
        }
    ]

    return (entry_id, returned)


def count():
    """The total amount of analytic events stored.

    This is used mainly for testing purposes.

    """
    log = get_log("count")

    conn = db.DB.conn()
    try:
        sql = (
            r"SELECT count(entry_id) FROM {} "
            r"WHERE time(1u) "
            r"GROUP BY time(1u) "
        ).format(
            TABLE_NAME
        )
        results = len(conn.query(sql))

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
    (entry_id, idbfmt) = influxdb_format(data)

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

    return entry_id


def get(entry_id):
    """Recover a specific anayltics event based on its unique id.

    :param entry_id: The unique analytic event id string.

    Not sure this is the best way but I'm only using this in testing at
    the moment.

    :returns: A dict of the found analytic event.

    If the entry_id was not found then ValueError will be raised.

    """
    log = get_log("get")

    assert entry_id

    conn = db.DB.conn()

    sql = (
        r"SELECT count(entry_id) FROM {} "
        r"WHERE time(1u) AND entry_id = '{}'"
        r"GROUP BY time(1u) "
    ).format(
        TABLE_NAME,
        entry_id,
    )
    log.debug("Looking for analytic event '{}'".format(entry_id))

    found = conn.query(sql)
    if not len(found):
        raise ValueError("Nothing found for entry_id '{}'".format(entry_id))

    item = found[0]
    data = dict(zip(item['columns'], item['points'][0]))
    log.debug("found for entry_id '{}': {}".format(entry_id, data))

    return data
