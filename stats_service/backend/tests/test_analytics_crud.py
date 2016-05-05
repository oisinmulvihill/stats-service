# -*- coding: utf-8 -*-
"""
Tests to exercise the influxdb storage back end.

Oisin Mulvihill
2015-01-30

"""
import datetime

#import pytest

from stats_service.backend import analytics


def test_analytics_logging_backend_api(logger, backend):
    """Test the backend CRUD api.

    """
    # nothing should be there initially:
    assert analytics.count("voting") == 0

    tags = {
        "uid": "user-86522",
        "event": "pnc.video.vote",
        "username": "sam270400",
        "competition_id": 1814,
        "http_user_agent": "PNC/3.2.2 (iPod touch; iOS 8.1; Scale/2.00)",
        "name": "sam270400",
        "competition_name": "Cutest Pets!!!",
        "datetime": "2015-11-11T15:37:07",
        "app_node": "app-04",
        "location": "GB",
        "video_id": 25944,
        "video_title": "bunny shadow",
        "http_x_real_ip": "86.25.91.110",
    }

    fields = {
        "value": 1,
    }

    analytics.log([{
        "measurement": "voting",
        "tags": tags,
        "fields": fields,
    }])

    assert analytics.count("voting") == 1

    # very basic querying, not super useful as there service is most for
    # writing the recovering data from:
    results = analytics.find("voting")
    assert len(results) == 1
    results = results[0]

    # tags type is lost, everything is a string:
    assert results['uid'] == "user-86522"
    assert results['video_id'] == "25944"
    assert results['competition_id'] == "1814"

    # field type is preserved:
    assert results['value'] == 1

    assert len(analytics.find("voting", event='pnc.video.vote')) == 1
    assert len(analytics.find("voting", not_in_keys='stuff')) == 0
    assert len(analytics.find("voting", competition_id='1814')) == 1
