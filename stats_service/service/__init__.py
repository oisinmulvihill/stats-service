# -*- coding: utf-8 -*-
"""
REST Service 'stats-service'

"""
import logging
import httplib
import pkg_resources

import raven
from pyramid.config import Configurator
from pp.web.base import restfulhelpers

from stats.backend import db
from stats.service.authorisation import api_access_token_middleware


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    log = get_log("main")

    sentry_client = None
    pkg = pkg_resources.get_distribution('stats-service')
    dsn = settings.get("sentry.dsn")
    if dsn:
        log.debug("Setting up sentry.")
        sentry_client = raven.Client(
            dsn=dsn,
            # inform the client which parts of code are yours
            include_paths=['stats'],
            # pass along the version of your application
            release=pkg.version,
        )
        log.info("Sentry client configured OK.")

    else:
        log.warn("Nothing found for 'sentry.dsn' in config. Sentry disabled.")

    config = Configurator(settings=settings)

    log.debug("Setting up databse configuration with prefix 'influxdb.'")
    db.DB.init(settings, prefix='influxdb.')

    not_found = restfulhelpers.xyz_handler(httplib.NOT_FOUND)
    config.add_view(not_found, context='pyramid.exceptions.NotFound')

    bad_request = restfulhelpers.xyz_handler(httplib.BAD_REQUEST)
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
    config.scan("stats.service", ignore="stats.service.tests")

    # Make the pyramid app I'll then wrap in other middleware:
    app = config.make_wsgi_app()

    # RESTful helper class to handle PUT, DELETE over POST requests:
    app = restfulhelpers.HttpMethodOverrideMiddleware(app)

    # Only secure token only access to POST analytics:
    app = api_access_token_middleware(settings, app)

    # Should be last to catch all errors of below wsgi apps. This
    # returns useful JSON response in the body of the 500:
    app = restfulhelpers.JSONErrorHandler(app)

    app.pnc_sentry_client = sentry_client

    return app
