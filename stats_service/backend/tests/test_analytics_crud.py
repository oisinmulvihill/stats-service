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
    """Test providing and not providing event_id field.
    """
    event_id1 = analytics.eid()
    has_event_id_data = {
        "time": 1415793092000.01,
        "event_id": event_id1,
        "event": "test.evt"
    }
    now = datetime.datetime(2014, 11, 12, 11, 51, 32, 10)
    ts = analytics.unix_time_millis(now)

    eid, result = analytics.influxdb_format(has_event_id_data, now)

    assert event_id1 == eid

    d = dict(
        time=ts,
        event_id=event_id1,
        event='test.evt',
    )

    assert result[0]['fields']['time'] == d['time']
    assert result[0]['fields']['event_id'] == d['event_id']
    assert result[0]['fields']['event'] == d['event']
    assert result[0]['measurement'] == analytics.table_name()

    has_not_event_id_data = {
        "time": 1415793092000.01,
        "event": "test.evt.2"
    }

    eid, result = analytics.influxdb_format(has_not_event_id_data, now)
    assert eid
    assert "event_id" in result[0]['fields']
    assert result[0]['fields']['event_id'] == eid


def test_analytics_logging_backend_api(logger, backend):
    """Test the backend CRUD api.

    """
    # nothing should be there initially:
    assert analytics.count() == 0

    data = {
        "uid": "user-86522",
        "event": "pnc.video.vote",
        "username": "sam270400",
        "competition_id": '1814',
        "http_user_agent": "PNC/3.2.2 (iPod touch; iOS 8.1; Scale/2.00)",
        "name": "sam270400",
        "competition_name": "Cutest Pets!!!",
        "datetime": "2015-11-11T15:37:07",
        "app_node": "app-04",
        "location": "GB",
        "vote": '1',
        "video_id": '25944',
        "video_title": "bunny shadow",
        "http_x_real_ip": "86.25.91.110",
    }

    data2 = {
        "uid": "user-32790",
        "event": "status.update",
        "competition_id": '1814',
        "value": "happy",
        "http_x_real_ip": "86.25.91.110",
    }

    event_id1 = analytics.log(data)
    event_id2 = analytics.log(data2)

    assert analytics.count() == 2

    # very basic querying, not super useful as there service is most for
    # writing the recovering data from:
    results = analytics.find()
    assert len(results) == 2
    assert len(analytics.find(event='pnc.video.vote')) == 1
    assert len(analytics.find(not_in_keys='stuff')) == 0
    assert len(analytics.find(competition_id='1814')) == 2

    # a quick check of some fields
    entry = analytics.get(event_id1)

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
    assert entry['event_id'] is not None

    entry2 = analytics.get(event_id2)
    assert entry2['uid'] == data2['uid']
