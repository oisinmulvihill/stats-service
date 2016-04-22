# -*- coding: utf-8 -*-
"""
REST Service 'stats_service'

"""
import logging
import httplib

from pyramid.config import Configurator

from stats_service.backend import db
from stats_service.service.authorisation import init
from stats_service.service.authorisation import TokenMW
from stats_service.service.restfulhelpers import xyz_handler
from stats_service.service.restfulhelpers import JSONErrorHandler
from stats_service.service.restfulhelpers import HttpMethodOverrideMiddleware


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    log = get_log("main")

    config = Configurator(settings=settings)

    # configure basic token access
    identities = settings['stats_service.access.identities']
    log.info("Reading identities from file '{}'".format(identities))
    init(identities)

    log.debug("Setting up databse configuration with prefix 'influxdb.'")
    db.DB.init(settings, prefix='influxdb.')

    not_found = xyz_handler(httplib.NOT_FOUND)
    config.add_view(not_found, context='pyramid.exceptions.NotFound')

    bad_request = xyz_handler(httplib.BAD_REQUEST)
    config.add_view(
        bad_request,
        context='pyramid.httpexceptions.HTTPBadRequest'
    )

    # Maps to the status page:
    config.add_route('home', '/')

    config.add_route('log', '/log/event')
    config.add_route('log2', '/log/event/')

    config.add_route('event', '/log/event/{id}')
    config.add_route('event2', '/log/event/{id}/')

    config.add_route('ping', '/ping')
    config.add_route('ping2', '/ping/')

    # Testing clients for GET, PUT, POST, DELETE against out server:
    config.add_route('verb_test', '/verb/test/{id}')

    # Pick up the views which set up the views automatically:
    #
    config.scan("stats_service", ignore="stats_service.tests")

    # Make the pyramid app I'll then wrap in other middleware:
    app = config.make_wsgi_app()

    # RESTful helper class to handle PUT, DELETE over POST requests:
    app = HttpMethodOverrideMiddleware(app)

    # Only secure token only access to POST analytics:
    app = TokenMW(app)

    # Should be last to catch all errors of below wsgi apps. This
    # returns useful JSON response in the body of the 500:
    app = JSONErrorHandler(app)

    return app
