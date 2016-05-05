# -*- coding: utf-8 -*-
"""
Tests to verify the REST interface of the stats_service.

Oisin Mulvihill
2015-10-06

"""
#import pytest
import pkg_resources

from stats_service.backend import analytics


def test_service_is_running(logger, stats_service):
    """Test the service is running and the status it returns.
    """
    response = stats_service.api.ping()

    pkg = pkg_resources.get_distribution("stats-service")

    assert response["status"] == "ok"
    assert response['name'] == "stats-service"
    assert response['version'] == pkg.version


def test_log_event(logger, stats_service):
    """Log a single event and check it is present.
    """
    response = stats_service.api.ping()
    assert response["status"] == "ok"

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

    stats_service.api.log([{
        "measurement": "voting",
        "tags": tags,
        "fields": fields,
    }])

    assert analytics.count("voting") == 1

    # The is no GET api at the moment have a quick look in the backend and
    # see its ok:
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

    # call example metric system_startup()
    #
    assert len(analytics.find("server_startup")) == 0
    assert analytics.count("server_startup") == 0

    stats_service.api.system_startup()

    assert analytics.count("server_startup") == 1
    results = analytics.find("server_startup")
    assert len(results) == 1
    results = results[0]
    assert 'uid' in results
