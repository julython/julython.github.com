
The Lazy Guide to Websockets
============================

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

Class Based Generic View?
--------------------------

.. code-block:: python

	class UserProfile(detail.DetailView):
	    model = User
	    slug_field = 'username'
	    slug_url_kwarg = 'username'
	    context_object_name = 'profile'

Template
---------

Generic Views move the DB queries to the template.

.. code-block:: django

	<h1>{{ object }}</h1>
	<ul>
	  {% for commit in object.commit_set.all %}
	    <li>{{ commit }}</li>
	  {% endfor %}
	</ul>

Problems
--------

* Still has multiple blocking DB queries.
* Template logic hides DB queries.

Solution
========

* Lazy load related objects with Ajax.
* Build an API.
* Build a dynamic UI.

Tastypie
========

* Simple RESTful API Generation.

Example
-------

here

More
----

here

Backbone and Knockout
=======================

* Backbone handles all interaction with API.
* Knockout provides a simple declarative 2-way binding.

Example
-------

Here

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
	    nginx version: nginx/1.2.6
	
	# test configuration
	sudo nginx -c $PUSH_PATH/misc/nginx.conf -t
	    the configuration file $PUSH_PATH/misc/nginx.conf syntax is ok
	    configuration file $PUSH_PATH/misc/nginx.conf test is successful
	
	# run
	sudo nginx -c $PUSH_PATH/misc/nginx.conf

Configuration
-------------

.. code-block:: nginx

	# TOP LEVEL MESSAGING CONFIGURATION
	push_stream_ping_message_text '""';
	
	## SERVER CONFIGURATION ##
	## ==================== ##
	server {
		# INSERT STANDARD GLOBAL CONFIG HERE
		
		# MESSAGING CONFIGURATION
		# =======================
		push_stream_ping_message_interval 10s;
		push_stream_content_type "application/json; charset=utf-8";		
		push_stream_message_template "{
		   \"id\":~id~,
		   \"channel\":\"~channel~\",
		   \"text\":~text~,
		   \"tag\":~tag~,
		   \"time\":\"~time~\"}";

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