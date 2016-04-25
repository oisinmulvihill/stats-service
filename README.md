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

    # https://github.com/monitoringartist/grafana-xxl
    #
    # grafana storage:
    docker stop grafana-storage ; docker rm grafana-storage ; docker run -dt -v $HOME/grafana:/var/lib/grafana --name grafana-storage busybox:latest

    # Grafana interface, persisting set up to disk:
    docker stop grafana ; docker rm grafana ; docker run \
        -d \
        --restart=always \
        --name=grafana \
        -p 3000:3000 \
        --link grafana-storage \
        --volumes-from grafana-storage \
      monitoringartist/grafana-xxl

Run the stats-service to start collecting measurements::

    # Now run the stats-service
    cd $SRCDIR/stats_service
    pserve development.ini


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

    # The access token from a user in the access.json file the server uses:
    TOKEN="eyJleHBpcmVzIjogMTAsICJzYWx0IjogImJjODIxOCIsICJpZGVudGl0eSI6ICJzdGF0c2JvYiJ9NyjnVy3QkN9pa2H_DVe4OZLi5dydu1mB3clN2HezjI8y331ZflOHSOtgvw8JjnjlC4UFF8q1LCp0kHdj96ipDw=="

    # Basic payload, the "event" & "uid" fields are required the rest are
    # optional
    DATA='{"event": "pnc.test", "uid": "oisin", "now": "'"$(date)"'"}'

    curl -H "Accept: application/json" \
         -H "Content-Type: application/json" \
         -H "Authorization: Token $TOKEN" \
         -X POST \
         -d "$DATA" \
         http://www.pnc:20080/log/event/

    "entry_4a42fcc243884bb58cb6d00759c2955d"

In this example the REST service is running on my vagrant devbox. The REST
stats-service primary purpose is to log events. Individual events can be
recovered, however there is no querying API. This is where Grafana or the
InfluxDB admin interface come in. A basic example recovering above event via
the API is::

.. sourcecode:: bash

    curl -H "Content-Type: application/json" \
         -H "Authorization: Token $TOKEN" \
         -X GET \
         http://www.pnc:20080/log/event/entry_d53a4f0bd16341e7a2ce86aaeec99d21

    {"uid": "oisin", "event_id": "entry_d53a4f0bd16341e7a2ce86aaeec99d21", "hostname": null, "datetime": null, "time": "2016-04-25T12:29:48.844949259Z", "now": "Mon 25 Apr 2016 13:29:48 BST", "event": "pnc.test"}


REST API
~~~~~~~~


GET /ping
`````````

Test the service is active and return the current version number. This is
mainly provided to aid monitoring services.

.. sourcecode:: bash

    $ curl -X GET http://www.pnc:20080/ping/
    {"status": "ok", "version": "1.0.0", "name": "stats-service"}


POST /log/event
```````````````

Log an analytic event which is stored into InfluxDB via the
stats_service.backend.analytics.log(data) function. The analytics event JSON
will be passed as a dict to log(). This data dictionary must contain at least
uid and event fields.

The 'uid' field is the unique id used to tie analytic events together as part
of the same session. It can be empty but the field is required.

The 'event' field is the the end user classification string of the event. For
example 'pnc.user.login'.

The 'time' epoch timestamp will be added automatically to the data. There
will also be an 'entry_<UUID4>' id given to the specific event.

Other fields present will be stored without any further processing. The data
needs to JSON-able and field names can't have anything other then alphanumeric
characters in them. This is an InfluxDB restriction.

The events are stored in a measurement called "analytics" in InfluxDB. On the
server side. The environment variable TABLE_NAME is used. If its empty
"analytics" is used by default. The measurement or table will be created when
the first event is logged.

.. sourcecode:: bash

    # The access token from a user in the access.json file the server uses:
    TOKEN="eyJleHBpcmVzIjogMTAsICJzYWx0IjogImJjODIxOCIsICJpZGVudGl0eSI6ICJzdGF0c2JvYiJ9NyjnVy3QkN9pa2H_DVe4OZLi5dydu1mB3clN2HezjI8y331ZflOHSOtgvw8JjnjlC4UFF8q1LCp0kHdj96ipDw=="

    # Basic payload, the "event" & "uid" fields are required the rest are
    # optional
    DATA='{"event": "pnc.test", "uid": "oisin", "now": "'"$(date)"'"}'

    curl -H "Accept: application/json" \
         -H "Content-Type: application/json" \
         -H "Authorization: Token $TOKEN" \
         -X POST \
         -d "$DATA" \
         http://www.pnc:20080/log/event/

    "entry_4a42fcc243884bb58cb6d00759c2955d"


stats-client
------------

The Python stats-client library is very straight forward to use. The follow is
an example of its usage. The idea is you create your own in-house stats-client
library and use this one as a base for the authentication set up.

I have created my own-in house version to track purchases and tie it with
google channels. I track login and logout failures to see early warnings of
problems. In the past I've used it to track image encoding Jobs running
Celery. I was able to see if the worker queue were growing and if the workers
were failing.

Set Up
~~~~~~

The library needs to be configured with the correct end point:

.. sourcecode:: python

    # Import the client library then configure it with the correct end point:
    from stats_client.client.analytics import Analytics

    # http://localhost:20800" is the service running on the devbox:
    Analytics.init(dict(
        url="http://localhost:20800",
        access_token="<token data>",
        defer=False | True
    ))

The defer field is used to indicate you wish to wait for the event to
successfully POST and the server return. If this is True then a thread will
take over the actually logging of the event and immediately return.


Usage
~~~~~

Now from anywhere in the code you can log events. As an example of a custom
event, I've created a simple system startup call. I use this in all of my
services. I can then see from grafana dashboard what is going on, are any
services constantly restarting.

.. sourcecode:: python

    from stats_client.client.analytics import Analytics

    # Log that the application has started.
    Analytics.stats().system_startup()

The Analytics class provides many methods which can be used. The stats()
function returns the instance configured Analytics by a call to init({...}).

Behind the scene the system_startup wraps a call to log(). It looks like:

.. sourcecode:: python

    import socket
    from stats_client.client.analytics import Analytics

    api = Analytics.stats()

    data = dict(
        event='server.start',
        uid="system-{}".format(self.app_node),
        ip=socket.gethostbyname(self.app_node),
        app_node=self.app_node,
    )

    api.log(data)

The event is a string and i have have a format i use for this. You are free to
choose your own. The 'uid' in this case will be used to collect all events
for that specific system. In the above case uid would become 'system-devbox'
running off my vagrant devbox. In production this would be the hostname of the
machine/VM/docker container/etc. In the above example self.app_node is set to
the system hostname when the Analytics is instanciated.
