stats_service
=============

Analytics Gathering REST API Endpoint for storing metrics in InfluxDB. Valid
https://github.com/oisinmulvihill/apiaccesstoken Tokens are needed to talk to
the service. The secret and access_token are set up in configuration.

Dev Env Set Up
--------------

Get the current GitHub dependancies::

    SRCDIR=~/src

    # testing deps:
    git clone https://github.com/oisinmulvihill/evasion-common.git
    git clone https://github.com/oisinmulvihill/pytest-docker-service-fixtures.git
    git clone https://github.com/oisinmulvihill/pytest-docker-service-fixtures.git

    # app deps:
    git clone https://github.com/oisinmulvihill/apiaccesstoken.git
    git clone https://github.com/oisinmulvihill/stats-client.git
    git clone https://github.com/oisinmulvihill/stats_service.git

Set up steps::

    mkvirtualenv --clear stats

    SRCDIR=~/src

    cd $SRCDIR/apiaccesstoken
    python setup.py develop

    cd $SRCDIR/evasion-common
    python setup.py develop

    cd $SRCDIR/docker-testingaids
    python setup.py develop

    cd $SRCDIR/pytest-docker-service-fixtures
    python setup.py develop

    cd $SRCDIR/stats-client
    python setup.py develop

    cd $SRCDIR/stats_service
    python setup.py develop


docker images::

    # download if not present and (re)start the influxdb container:
    docker rm -f influxdb 2>/dev/null
    docker run --name=influxdb -d -p 8083:8083 -p 8086:8086 tutum/influxdb:latest



REST API
--------

I'm currently making public the REST Endpoint and basic client library I use to
gather internal analytic metrics. The secret sauce lies not in the basic client
and service. It lies more in the metrics gathers, processed and visualisation
of InfluxDB data. I'll explain this in more details.

Analytics is used to gain insights into how people are using our product.
There are several stages to get to this point which form a pipeline. Generally
these steps are gathering the raw analytics, processing and finally
presentation. Analytics can provide insights into how are systems are also
working and so compliment any monitoring peformed. The REST service which we
log analytic events to. For example:

.. sourcecode:: bash

    $ DATA='{"event": "pnc.test", "uid": "oisin", "now": "'"$(date)"'"}'
    $ curl -X POST -d "$DATA" http://www.pnc:20080/log/event/
    "entry_4a42fcc243884bb58cb6d00759c2955d"

In this example the REST service is running on the :ref:`devbox <devbox>` is used.
Logging manually like this is not ideal. Instead for Python applications the
:ref:`Python stats client library <pncstatsclientrepo>` is used. This makes
sure the required fields are present and provides standard event names without
having to bother the end user with the details.

The REST service is only used to log events. It is not intended for use in
reporting or recoverying the events.


REST API
~~~~~~~~

The API doesn't have any authentication. I'm planning to switch this soon over
to Token access once http://stuff> is public. If your
using Python use the pnc-stats-client library instead. Ideally every language
we use should wrap the api and make it nice :)


GET /ping
`````````

Test the service is active and return the current version number. This is
mainly provided to aid monitoring services.

.. sourcecode:: bash

    $ curl -X GET http://www.pnc:20080/ping/
    {"status": "ok", "version": "1.0.0", "name": "stats_service"}


POST /log/event
```````````````

Log an analytic event which is stored into :ref:`InfluxDB <influxdburi>` via the
pnc.stats_service.backend.analytics.log(data) function. The analytics event JSON will
be passed as a dict to log(). This data dictionary must contain at least uid
and event fields.

The 'uid' field is the unique id used to tie analytic events together as part
of the same session. It can be empty but the field is required.

The 'event' field is the the end user classification string of the event. For
example 'pnc.user.log'.

The 'time' epoch timestamp will be added automatically to the data. There
will also be an 'entry_<UUID4>' id given to the specific event.

Other fields present will be stored without any further processing. The data
needs to JSON-able and field names can't have anything other then alphanumeric
characters in them. This is an :ref:`InfluxDB <influxdburi>` restriction.

The events are stored in a timeseries called "analytics" in :ref:`InfluxDB <influxdburi>`.

.. sourcecode:: bash

    $ DATA='{"event": "pnc.test", "uid": "oisin", "now": "'"$(date)"'"}'
    $ curl -X POST -d "$DATA" http://www.pnc:20080/log/event/
    "entry_4a42fcc243884bb58cb6d00759c2955d"


stats-client
------------

The :ref:`Python stats client library <pncstatsclientrepo>` is very straight
forward to use. The follow is an example of its usage.


Set Up
~~~~~~

.. _pncstatsclientsetup:

The library needs to be configured with the correct end point:

.. sourcecode:: python

    # Import the client library then configure it with the correct end point:
    from stats_client import analytics

    # http://localhost:20800" is the service running on the devbox:
    analytics.init(dict(
        access_token="<token data>",
        uri="http://localhost:20800",
    ))


Usage
~~~~~

Now from anywhere in the code you can log events, for example a system startup
of the api service:

.. sourcecode:: python

    from stats_client import stats

    # Log that the application has started.
    stats().system_startup()

The stats_client.analytics:Analytics class provides many methods which can
be used. The stats() function returns the instance configured Analytics by a
call to init({...}).
