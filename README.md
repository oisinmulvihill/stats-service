stats-service
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

    cd $SRCDIR/stats-service
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


Running the tests (re)using an exiting InfluxDB container::

    workon stats
    easy_install pytest docker-py

    # on devbox:
    export DK_CONFIG_FILE=$HOME/dk_config.yaml
    export DKInfluxDB_UseENV=yes
    export DKInfluxDB_PORT=8086
    export DKInfluxDB_HOST=localhost
    export DKInfluxDB_USER=root
    export DKInfluxDB_PASSWORD=root
    export DKInfluxDB_DB=test_analytics

    cd ~/src/stats-service

    py.test -sv


Server Authentication Set Up
----------------------------

The server looks for access.json to load the users and their token pairs. Don't
use the access.json in the Github stats-service repository. This is not secure
as everyone will have the keys for this. Instead generate an access.json using
the "accesshelper" command line tool::

    $ accesshelper --access_json=/tmp/access.json

    The file /tmp/access.json was written successfully for username 'statsbob'. The following
    access_token can be used:

    eyJleHBpcmVzIjogMTAsICJzYWx0IjogIjlkZGI1ZSIsICJpZGVudGl0eSI6ICJzdGF0c2JvYiJ9y6Grs3WUvo_6OTw62Q8ZjZ412hSdWQG7LME1eWVxxSeucmrhYyfJnuoXwygL_TYKLy6gMcOJ5PDpvEGEaAvGqw==

You can then set the server configuration to use this file. Set the [app:main]
section's stats_service.access.identities to absolute path to this new file.
For example in the above case this would become::

    [app:main]
    :

    stats_service.access.identities = /tmp/access.json

    :

Doing this will secure the service so only you can log events.


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
    DATA='[{"fields": {"value": 1}, "tags": {"from": "oisin"}, "measurement": "ping"}]'

    curl -H "Accept: application/json" \
         -H "Content-Type: application/json" \
         -H "Authorization: Token $TOKEN" \
         -X POST \
         -d "$DATA" \
         http://www.pnc:20080/log/event/

    "OK"

In this example the REST service is running on my vagrant devbox. The REST
stats-service primary purpose is to log events.

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
fields, tags and mesurement fields.

The events are stored in a measurement the user provides. The measurement
will be created when the first event is logged.

.. sourcecode:: bash

    # The access token from a user in the access.json file the server uses:
    TOKEN="eyJleHBpcmVzIjogMTAsICJzYWx0IjogImJjODIxOCIsICJpZGVudGl0eSI6ICJzdGF0c2JvYiJ9NyjnVy3QkN9pa2H_DVe4OZLi5dydu1mB3clN2HezjI8y331ZflOHSOtgvw8JjnjlC4UFF8q1LCp0kHdj96ipDw=="

    # Basic payload, the "event" & "uid" fields are required the rest are
    # optional
    DATA='[{"fields": {"value": 1}, "tags": {"from": "oisin"}, "measurement": "ping"}]'

    curl -H "Accept: application/json" \
         -H "Content-Type: application/json" \
         -H "Authorization: Token $TOKEN" \
         -X POST \
         -d "$DATA" \
         http://www.pnc:20080/log/event/

    "OK"


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

    points = [dict(
        measurement='server_startup',
        tags=dict(
            uid="system-{}".format(self.app_node),
            ip=socket.gethostbyname(self.app_node),
            hostname=self.app_node,
        ),
        fields=dict(
            # will allow you to count/avg/min/max the number of startups.
            # lots/<time period e.g. min,day,etc> is probably bad :)
            value=1
        )
    )]

    api.log(points)

In the above case uid would become 'system-devbox' running off my vagrant
devbox. In production this would be the hostname of the machine/VM/container/etc.
In the above example self.app_node is set to the system hostname when the
Analytics is instanciated.
