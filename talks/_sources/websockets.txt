.. _websockets:

The Lazy Guide to Websockets
============================

Jan 24th, 2013

by Robert Myers

robert@julython.org

Story
-----------

* Look at a simple Django App.
* Add fancy UI with endless scroll.
* Keep the page up todate.

Simple Django View
==================

Views.py
--------

.. code-block:: python

    def projects(request, username):
        user = get_object_or_404(User, username=username)
        projects = user.projects.all()
        commits = Commit.objects.filter(user=user)
    
        return render_to_response('projects.html', {
                'projects': projects,
                'profile': user,
                'commits': commits,
            },
            context_instance=RequestContext(request))

Problems
--------

* Multiple blocking DB queries in view logic.
* Manual pagination.
* Repeatitive boilerplate.

Solution
========

* Lazy load related objects with Ajax.
* Build an API.
* Build a dynamic UI.

Tastypie
========

* Simple RESTful API Generation.

Example Resource
-----------------

.. code-block:: python

    class CommitResource(ModelResource):
        user = fields.ForeignKey(UserResource, 'user', 
                                 blank=True, null=True)
        project = fields.ForeignKey(ProjectResource, 'project', 
                                    blank=True, null=True)
    
        class Meta:
            queryset = Commit.objects.all()
            queryset.select_related('user', 'project')
            allowed_methods = ['get']
            filtering = {
                'user': ALL_WITH_RELATIONS,
                'project': ALL_WITH_RELATIONS,
                'timestamp': ['exact', 'range', 'gt', 'lt'],
            }

Example URLs
-------------

.. code-block:: python

    from tastypie.api import Api
    from july import api
    v1_api = Api(api_name='v1')
    v1_api.register(api.CommitResource())
    
    urlpatterns += patterns('',
        url(r'^api/', include(v1_api.urls)),
    )

* GET /api/v1/commit/
* GET /api/v1/commit/(object_id)/
* GET /api/v1/commit/schema/

Example Output
----------------

.. code-block:: javascript

    {
        meta: {
            limit: 1,
            next: "/api/v1/commit/?format=json&limit=1&offset=3",
            offset: 2,
            previous: "/api/v1/commit/?format=json&limit=1&offset=1",
            total_count: 11
        },
        objects: [
            {
                created_on: "2013-01-18T06:26:39.349473",
                hash: "61ef4c52d9731b8f03240961834f3b1d4fa6cd53",
                message: "Adding a fabric command to load test commits",
                other: "Fields here"
            }
        ]
    }
        

Backbone and Knockout
=======================

* Backbone handles all interaction with API.
* Knockout provides a simple declarative 2-way binding.

Backbone Collection
--------------------

.. code-block:: javascript

    JULY.CommitCollection = Backbone.Collection.extend({
      model: JULY.Commit,
      url: function() {return '/api/v1/commit/?' + this.params();},
      initialize: function(data, options) {
        this.limit = options.limit || 20;
        this.offset = options.offset || 0;
      },
      params: function() {
        return jQuery.param({limit: this.limit, offset: this.offset});
      },
      parse: function(resp) {
        this.total = resp.meta.total_count;
        this.offset = resp.meta.offset + this.limit;
        return resp.objects;
      }
    });

Knockback
----------

Glue between Backbone and Knockout.

.. code-block:: javascript

    JULY.CommitsView = JULY.ViewModel.extend({
      initialize: function(options) {
        this.c = new JULY.CommitCollection(null, options);
        this.c.fetch({add: true});
        this.commits = kb.collectionObservable(this.c);
      },
      hasMore: function() {
        return this.commits.collection().hasMore;
      },
      fetch: function(){
        if (this.hasMore()) {
          this.commits.collection().fetch({add:true});
        }
      }
    });

Knockout In Template
---------------------

.. code-block:: html

    <div data-bind="foreach: commits">
      <div class="media">
        <a class="thumbnail pull-left" data-bind="attr:{href: link}">                    
          <img data-bind="attr: {src: picture_url, alt: username}" />
        </a>
        <div class="media-body">
        <h4 class="media-heading" data-bind="timeago: timestamp"></h4>
        <strong data-bind="text: message"></strong>
        <p class="hash" data-bind="visible: username">
          <a data-bind="text: username, attr: {href: link }"></a> &mdash;
          <a data-bind="visible: url, attr:{href:url }">
            <span data-bind="text: hash().substring(0, 8)"></span>
          </a>
        </p>
        <p class="hash" data-bind="visible: !username()">
          <span data-bind="visible: !url(), text: hash().substring(0, 8)"></span>
        </p>
          </div>
      </div>
    </div>

Knockout Continued
------------------

Connect the page up to the collection:

.. code-block:: html

    <script type="text/javascript">
      ko.applyBindings(new JULY.CommitsView());
    </script>

Realtime
========

Time to get real!

Choices
-------

* Gevent
* Tornado
* Twisted
* Nginx Push Stream

Nginx Push Stream Module
========================

http://www.nginxpushstream.com/

Benefits
--------

* You are already running Nginx (I hope)
* Minimal changes to your application
* Simple low security pub/sub model.
* Supports: web sockects, long polling, event source, stream
* Low overhead (confirable memory usage)
* Publish messages with simple POST

Building
--------

You have to build it yourself:

.. code-block:: bash

    # clone the project
    git clone http://github.com/wandenberg/nginx-push-stream-module.git
    PUSH_PATH=$PWD/nginx-push-stream-module
    
    wget http://nginx.org/download/nginx-1.2.6.tar.gz
    
    # unpack, configure and build
    tar xzvf nginx-1.2.6.tar.gz
    cd nginx-1.2.6
    ./configure --prefix=/etc/nginx --conf-path=/etc/nginx/nginx.conf \
    --add-module=../nginx-push-stream-module
    make

Building cont.
--------------

.. code-block:: bash

    # install and finish
    sudo make install
    
    # check
    sudo nginx -v
    > nginx version: nginx/1.2.6
    
    # test configuration
    sudo nginx -c $PUSH_PATH/misc/nginx.conf -t
    > the configuration file $PUSH_PATH/misc/nginx.conf syntax is ok
    > configuration file $PUSH_PATH/misc/nginx.conf test is successful
    
    # run
    sudo nginx -c $PUSH_PATH/misc/nginx.conf

Configuration
-------------

.. code-block:: nginx

    # TOP LEVEL MESSAGING CONFIGURATION
    push_stream_ping_message_text '""';
    
    ## SERVER CONFIGURATION ##
    server {
        push_stream_ping_message_interval 10s;
        push_stream_content_type "application/json; charset=utf-8";
        # simplified Template    
        push_stream_message_template "{\"text\":~text~\"\}";
        
        # LOCATIONS HERE
    }

Web Sockets
-----------

.. code-block:: nginx

    # Subscription for Websockets via nginx-push-stream-module
    location ~ /events/ws/(.*) {
        push_stream_websocket;
        push_stream_websocket_allow_publish off;
        set $push_stream_channels_path $1;
    }

EventSource
-----------

.. code-block:: nginx

    # Subscription for EventSource with nginx-push-stream-module
    location ~ /events/ev/(.*) {
        push_stream_subscriber;
        push_stream_eventsource_support on;
        set $push_stream_channels_path $1;
    }

Long Polling
------------

.. code-block:: nginx

    # Subscription for messaging system with nginx-push-stream-module
    location ~ /events/lp/(.*) {
        push_stream_subscriber long-polling;
        set $push_stream_channels_path $1;
    }

Stream
------

.. code-block:: nginx

    # iFrame streaming for messaging system with nginx-push-stream-module
    location ~ /events/sub/(.*) {
        push_stream_subscriber;
        set $push_stream_channels_path $1;
    }

Stats
-----

See how many connections are open and how many messages there are:

.. code-block:: nginx

    # Messaging Channel Stats
    location ~ /events/stats/(.*) {
        push_stream_channels_statistics;
        set $push_stream_channel_id $1;
    }

Publishing Messages
-------------------

.. code-block:: nginx

    # Publish interface for messaging system
    location ~ /events/pub/(.*) {
        # only allow on the local server (readonly clients)
        allow 127.0.0.1;
        deny all;
        push_stream_publisher admin;
        set $push_stream_channel_id $1;
    }

Example Usage
-------------

Subscribe::

    curl -v 'http://localhost/events/sub/channel'

Publish::

    curl -X POST 'http://localhost/events/pub/channel' -d 'Hello!'

Creating Messages from Django
==============================

POST a message to the channel(s) you want.

*hint: just use Requests* 

Re-use Tastypie Resources
-------------------------

.. code-block:: python

	url = 'http://localhost/events/pub/'
	resource = CommitResource()
	# Build a bundle from the new object
	bundle = resource.build_bundle(obj=commit)
	# Run full_dehydrate to run all custom dehydrate methods 
	dehydrated = resource.full_dehydrate(bundle)
	serialized = resource.serialize(
	    None, dehydrated, format='application/json')
	# Make messages
	requests.post(url + 'user-%s' % commit.user.id, serialized)
	requests.post(url + 'project-%s' % commit.project.id, serialized)
	requests.post(url + 'global', serialized)

Tastypie allready serializes your content to JSON, so just use that. The
above code is run after a new commit object is created.
