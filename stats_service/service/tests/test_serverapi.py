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
    assert analytics.count() == 0

    data = {
        # required:
        "uid": "user-86522",
        "event": "pnc.user.view",
        # optional:
        "http_user_agent": "FlappyBird/1.0 (iPod touch; iOS 8.1; Scale/2.00)",
        "app_node": "super-node-04",
        "location": "GB",
        "http_x_real_ip": "86.25.91.110",
    }

    # Create a new event:
    event_id = stats_service.api.log(data)

    assert event_id is not None

    assert analytics.count() == 1

    # The is no GET api at the moment have a quick look in the backend and
    # see its ok:
    entry = analytics.get(event_id)

    assert entry['uid'] == data['uid']
    assert entry['event'] == data['event']
    assert entry['http_user_agent'] == data['http_user_agent']
    assert entry['app_node'] == data['app_node']
    assert entry['location'] == data['location']
    assert entry['http_x_real_ip'] == data['http_x_real_ip']

    # extra fields which should be present and not empty after logging:
    assert 'time' in entry
    assert 'event_id' in entry
