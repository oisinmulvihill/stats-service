# -*- coding: utf-8 -*-
"""
stats_service

This provides the views which are used in the dispatch routing set up.

"""
import logging
import pkg_resources

from pyramid.view import view_config

from stats_service.backend import analytics
from stats_service.service.authorisation import Access


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


@view_config(route_name='home', request_method='GET', renderer='json')
@view_config(route_name='ping', request_method='GET', renderer='json')
@view_config(route_name='ping2', request_method='GET', renderer='json')
def status(request):
    """This is used to 'ping' the web service to check if its running.

    :returns: a status dict which the configured view will return as JSON.

    The dict has the form::

        dict(
            status="ok",
            name="<project name>",
            version="<egg version of stats_service>"
        )

    """
    pkg = pkg_resources.get_distribution('stats_service')

    return dict(
        status="ok",
        name="stats_service",
        version=pkg.version,
    )


@view_config(route_name='log', request_method='POST', renderer="json")
@view_config(route_name='log2', request_method='POST', renderer="json")
@Access.auth_required
def log_event(request):
    """Log the JSON body object as an analytic event.

    This will be passed directly to stats_service.backend.analytics.log().

    :returns: The entry_id of the created event.

    """
    log = get_log('log_event')
    try:
        log.debug("looking for JSON body.")
        data = request.json_body

    except ValueError:
        # no data present
        log.error("no JSON body found.")
        data = {}

    log.debug("logging received data: {}".format(data))

    entry_id = analytics.log(data)

    log.debug("event logged its unique id is '{}'".format(entry_id))

    return entry_id


@view_config(route_name='event', request_method='GET', renderer="json")
@view_config(route_name='event2', request_method='GET', renderer="json")
@Access.auth_required
def recover_event(request):
    """Recover the contents of a specific event.

    This will return the results of stats_service.backend.analytics.get(id).

    :returns: The event data stored.

    """
    log = get_log('recover_event')

    event_id = request.matchdict['id'].strip().lower()
    log.debug("Looking for event with id '{}'".format(event_id))

    event_data = analytics.get(event_id)

    log.debug("event data recovered: '{}'".format(event_data))

    return event_data
