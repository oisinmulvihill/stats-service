# -*- coding: utf-8 -*-
"""
Useful classes and methods to aid RESTful webservice development in Pyramid.

PythonPro Limited
2012-01-14

"""
import json
import httplib
import logging
import traceback
#from decorator import decorator

from pyramid.request import Response


def get_log(e=None):
    return logging.getLogger("{0}.{1}".format(__name__, e) if e else __name__)


def json_result(view_callable):
    """Return a result dict for a response.

      rc = {
          "success": True | False,
          "data": ...,
          "message", "ok" | "..message explaining result=False..",
      }

    the data field will contain whatever is returned from the response
    normal i.e. any valid type.

    """
    #log = get_log('json_result')

    def inner(request, *args):
        """Add the success status wrapper. exceptions will be
        handled elsewhere.
        """
        response = dict(success=True, data=None, message="ok")
        response['data'] = view_callable(request, *args)
        return response

    return inner


def status_body(
    success=True, data=None, message="", to_json=False, traceback='',
):
    """Create a JSON response body we will use for error and other situations.

    :param success: Default True or False.

    :param data: Default "" or given result.

    :param message: Default "ok" or a user given message string.

    :param to_json: Default True, return a JSON string or dict is False.

    the to_json is used in situations where something else will take care
    of to JSON conversion.

    :returns: JSON status response body.

    The default response is::

        json.dumps(dict(
            success=True | False,
            data=...,
            message="...",
        ))

    """
    # TODO: switch tracebacks off for production
    body = dict(
        success=success,
        data=data,
        message=message,
    )

    if traceback:
        body['traceback'] = traceback

    if to_json:
        body = json.dumps(body)

    return body


def status_err(exc, tb):
    """ Generate an error status response from an exception and traceback
    """
    return status_body("error", str(exc), exc.__class__.__name__, tb,
                       to_json=False)


#@decorator
def status_wrapper(f, *args, **kw):
    """ Decorate a view function to wrap up its response in the status_body
        gumph from above, and handle all exceptions.
    """
    try:
        res = f(*args, **kw)
        return status_body(message=res, to_json=False)
    except Exception, e:
        tb = traceback.format_exc()
        get_log().exception(tb)
        return status_err(e, tb)


def notfound_404_view(request):
    """A custom 404 view returning JSON error message body instead of HTML.

    :returns: a JSON response with the body::

        json.dumps(dict(error="URI Not Found '...'"))

    """
    msg = str(request.exception.message)
    get_log().info("notfound_404_view: URI '%s' not found!" % str(msg))
    request.response.status = httplib.NOT_FOUND
    request.response.content_type = "application/json"
    body = status_body(
        success=False,
        message="URI Not Found '%s'" % msg,
    )
    return Response(body)


def xyz_handler(status):
    """A custom xyz view returning JSON error message body instead of HTML.

    :returns: a JSON response with the body::

        json.dumps(dict(error="URI Not Found '...'"))

    """
    log = get_log()

    def handler(request):
        msg = str(request.exception.message)
        log.info("xyz_handler (%s): %s" % (status, str(msg)))
        #request.response.status = status
        #request.response.content_type = "application/json"
        body = status_body(
            success=False,
            message=msg,
            to_json=True,
        )

        rc = Response(body)
        rc.status = status
        rc.content_type = "application/json"

        return rc

    return handler


# Reference:
#  * http://zhuoqiang.me/a/restful-pyramid
#
class HttpMethodOverrideMiddleware(object):
    '''WSGI middleware for overriding HTTP Request Method for RESTful support
    '''
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        if 'POST' == environ['REQUEST_METHOD']:
            override_method = ''

            # First check the "_method" form parameter
            # if 'form-urlencoded' in environ['CONTENT_TYPE']:
            #     from webob import Request
            #     request = Request(environ)
            #     override_method = request.str_POST.get('_method', '').upper()

            # If not found, then look for "X-HTTP-Method-Override" header
            if not override_method:
                override_method = environ.get(
                    'HTTP_X_HTTP_METHOD_OVERRIDE', ''
                ).upper()

            if override_method in ('PUT', 'DELETE', 'OPTIONS', 'PATCH'):
                # Save the original HTTP method
                method = environ['REQUEST_METHOD']
                environ['http_method_override.original_method'] = method
                # Override HTTP method
                environ['REQUEST_METHOD'] = override_method

        return self.application(environ, start_response)


class JSONErrorHandler(object):
    """Capture exceptions usefully and return to aid the client side.

    :returns: status_body set for an error.

    E.g.::

        rc = {
            "success": True | False,
            "data": ...,
            "message", "ok" | "..message explaining result=False..",
        }

    the data field will contain whatever is returned from the response
    normal i.e. any valid type.

    """
    def __init__(self, application):
        self.app = application
        self.log = get_log("JSONErrorHandler")

    def formatError(self):
        """Return a string representing the last traceback.
        """
        exception, instance, tb = traceback.sys.exc_info()
        error = "".join(traceback.format_tb(tb))
        return error

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)

        except Exception, e:
            self.log.exception("error: ")
            ctype = environ.get('CONTENT_TYPE')
            if ctype == "application/json":
                self.log.debug("Request was in JSON responding with JSON.")
                errmsg = "%d %s" % (
                    httplib.INTERNAL_SERVER_ERROR,
                    httplib.responses[httplib.INTERNAL_SERVER_ERROR]
                )
                start_response(errmsg, [('Content-Type', 'application/json')])
                message = str(e)
                error = "%s" % (type(e).__name__)
                self.log.error("%s: %s" % (error, message))
                return status_body(
                    success=False,
                    # Should this be disabled on production?
                    data=self.formatError(),
                    message=message,
                    # I need to JSON encode it as the view never finished and
                    # the requestor is expecting a JSON response status.
                    to_json=True,
                )

            else:
                raise
