# -*- coding: utf-8 -*-
"""
Tests to exercise the influxdb storage back end.

Oisin Mulvihill
2015-01-30

"""
import datetime

#import pytest

from stats_service.backend import analytics


def test_dict_to_influxformat(logger):
    """Test the conversion of a dict into the influxdb write points format.
    """
    entry_id = analytics.eid()
    data = {
        "time": 1415793092000.01,
        "entry_id": entry_id,
        "username": "sam270400",
        "competition_id": 1814,
        "app_node": "app-04",
        "vote": 1,
        "video_id": 25944,
        "http_x_real_ip": "86.25.91.110",
    }
    now = datetime.datetime(2014, 11, 12, 11, 51, 32, 10)
    ts = analytics.unix_time_millis(now)

    fields = data.keys()
    fields.sort()

    entry_id2, result = analytics.influxdb_format(data, now, entry_id)

    d = dict(
        time=ts,
        entry_id=entry_id,
        username=data['username'],
        competition_id=data['competition_id'],
        app_node=data['app_node'],
        vote=data['vote'],
        video_id=data['video_id'],
        http_x_real_ip=data['http_x_real_ip'],
    )

    correct = [
        {
            "measurement": analytics.TABLE_NAME,
            "tags": d,
            "fields": d
        }
    ]

    assert result == correct


def test_analytics_logging_backend_api(logger, backend):
    """Test the backend CRUD api.

    """
    # nothing should be there initially:
    assert analytics.count() == 0

    data = {
        # required:
        "uid": "user-86522",
        "event": "pnc.video.vote",
        # optional:
        "username": "sam270400",
        "competition_id": 1814,
        "http_user_agent": "PNC/3.2.2 (iPod touch; iOS 8.1; Scale/2.00)",
        "name": "sam270400",
        "competition_name": "Cutest Pets!!!",
        "datetime": "2015-11-11T15:37:07",
        "app_node": "app-04",
        "location": "GB",
        "vote": 1,
        "video_id": 25944,
        "video_title": "bunny shadow",
        "http_x_real_ip": "86.25.91.110",
    }

    # Create a new event:
    entry_id = analytics.log(data)

    assert analytics.count() == 1

    # a quick check of some fields
    entry = analytics.get(entry_id)

    assert entry['uid'] == data['uid']
    assert entry['event'] == data['event']
    assert entry['username'] == data['username']
    assert entry['competition_id'] == data['competition_id']
    assert entry['http_user_agent'] == data['http_user_agent']
    assert entry['name'] == data['name']
    assert entry['competition_name'] == data['competition_name']
    assert entry['datetime'] == data['datetime']
    assert entry['app_node'] == data['app_node']
    assert entry['location'] == data['location']
    assert entry['vote'] == data['vote']
    assert entry['video_id'] == data['video_id']
    assert entry['video_title'] == data['video_title']
    assert entry['http_x_real_ip'] == data['http_x_real_ip']

    # extra fields which should be present and not empty after logging:
    assert entry['time'] is not None
    assert entry['entry_id'] is not None
