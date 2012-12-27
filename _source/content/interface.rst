Using Tastypie with Backbone and Knockout
=========================================

:author: Robert Myers
:date: 2012-12-27 20:12
:status: draft
:category: Code
:tags: python, javascript, knockback
:style: participating
:summary: The Julython UI has been updated to be more responsive 

Since July I have been working a little bit more on the UI side of the web. 
For `J(an)ulython`_ the site uses Tastypie_, Backbonejs_, Knockoutjs_ and 
Knockbackjs_ to display an endless scroll of commits. Because, this is what
all the cool kids are doing these days :) Let me explain each piece and how
we use them.

Tastypie
--------

From the site "Tastypie is an webservice API framework for Django. It provides 
a convenient, yet powerful and highly customizable, abstraction for creating 
REST-style interfaces." That about sums it up :) For Julython it just needed
a little bit of tweaking to get our api's up and running.

First you need to setup the api routing (urls):

.. code-block:: python

	# urls.py
	from django.conf.urls import patterns, include, url
	from tastypie.api import Api
	from july import api
	
	v1_api = Api(api_name='v1')
	v1_api.register(api.CommitResource())
	v1_api.register(api.ProjectResource())
	v1_api.register(api.UserResource())
	
	urlpatterns += patterns(
		url(r'^api/', include(v1_api.urls)),
	)

This sets up the following api urls:

* ``/api/v1/commit/``
* ``/api/v1/project/``
* ``/api/v1/user/``

Now I just need to add my Resources in the api module. The Project and User
resources are fairly simple as the defaults work just fine. The Commit
resource is only slightly more complex as I wanted to optimized the database
query a little bit. The commit resource also needs to create a gravatar image
for commits with no user. 

Here is what the ``api.py`` file looks like:

.. code-block:: python

	from tastypie.resources import ModelResource
	from tastypie.resources import ALL
	from tastypie.resources import ALL_WITH_RELATIONS
	from tastypie import fields
	
	from july.people.models import Commit, Project
	from july.models import User
	
	class UserResource(ModelResource):
	    
	    class Meta:
	        queryset = User.objects.all()
	        excludes = ['password', 'email', 'is_superuser', 'is_staff', 'is_active']
	
	class ProjectResource(ModelResource):
	    
	    class Meta:
	        queryset = Project.objects.all()
	
	class CommitResource(ModelResource):
	    user = fields.ForeignKey(UserResource, 'user', blank=True, null=True)
	    project = fields.ForeignKey(ProjectResource, 'project', blank=True, null=True)
	    
	    class Meta:
	    	queryset = Commit.objects.all().select_related('user', 'project')
	        allowed_methods = ['get']
	        filtering = {
	            'user': ALL_WITH_RELATIONS,
	            'project': ALL_WITH_RELATIONS,
	            'timestamp': ['exact', 'range', 'gt', 'lt'],
	        }

	    def gravatar(self, email):
	        """Return a link to gravatar image."""
	        url = 'http://www.gravatar.com/avatar/%s?s=48'
	        from hashlib import md5
	        email = email.strip().lower()
	        hashed = md5(email).hexdigest()
	        return url % hashed
	    
	    def dehydrate(self, bundle):
	        email = bundle.data.pop('email')
	        gravatar = self.gravatar(email)
	        bundle.data['project_name'] = bundle.obj.project.name
	        bundle.data['project_url'] = reverse('project-details', 
	            args=[bundle.obj.project.slug])
	        bundle.data['timestamp'] = date(bundle.obj.timestamp)
	        bundle.data['username'] = getattr(bundle.obj.user, 'username', None)
	        bundle.data['picture_url'] = getattr(bundle.obj.user, 
	                                             'picture_url', 
	                                             gravatar)
	        return bundle


The two interesting details here are the extra fields and the ``dehydrate`` 
method. First the ``fields.ForeignKey`` allow you to filter by the related
field. To make the the query more efficient be sure to add in the call to
``select_related('model_one', 'model_two')`` to the queryset. Next the 
``dehydrate`` method allows you to add in extra details not stored in the 
model. Here I am adding properties from the related models, and also setting
a default image with gravatar for commits from non-registered users. If you
like you can also pass ``full=True`` to the ``fields.ForeignKey`` to add all
the attributes from the related resource. 

Since we only need readonly access in the api this is all we need to do. 
There are many more options available so check it out. If you do wish to make
your Tastypie_ api's work well with backbone have a look at 
`backbone-tastypie`_.

Backbonejs
----------

Now that we have our REST-ful api we need to consume it. Backbonejs_ is a light
weight javascript library which provides models and collections that map to
you REST-ful api. The models and collections have attributes you can override
with custom functions making it very flexible.

The commit model is pretty basic here by default backbone will assume that the
resource will live at the ``urlRoot/id`` which is what we want:

.. code-block:: javascript

	/* Namespace all our custom objects */
	var JULY = JULY || {};
	
	JULY.Commit = Backbone.Model.extend({
		urlRoot: '/api/v1/commit/'
	});

The collection is slightly more complex. First we need to provide a constructor
function in order to pass in options. Our commit api can be filtered by
'project' or 'user', it also takes optional arguments for 'limit' and 'offset'.

.. code-block:: javascript

	JULY.CommitCollection = Backbone.Collection.extend({
		model: JULY.Commit,
		
		// Constructor method
		initialize: function(data, options) {
			this.projectId = options.projectId;
			this.userId = options.userId;
			this.limit = options.limit || 20;
			this.offset = options.offset || 0;
			this.total = 0; // set after fetch
			this.hasMore = false; // set after fetch
		},

.. note:: The first optional argument to the initialize function is always a 
   list of models. So you would create this collection like:
   ``var c = new JULY.CommitCollection(null, {limit: 100})``

Now we need to pass our arguments to the url so we need to create a url
function and a helper method to generate the query args:

.. code-block:: javascript

		// Custom url with query parameters added in
		url: function() {return '/api/v1/commit/?' + this.params()},
		
		// return the parameters for the url
		params: function() {
			var p = {limit: this.limit, offset: this.offset}
			if (this.projectId) {p.project = this.projectId}
			if (this.userId) {p.user = this.userId}
			return jQuery.param(p);
		},

The last part of the puzzle is how to parse the results from the fetch call:

.. code-block:: javascript

		// parse the results from the fetch() call.
		parse: function(resp) {
			this.total = resp.meta.total_count;
			this.offset = resp.meta.offset + this.limit;
			this.hasMore = this.total > this.models.length;
			return resp.objects;
		}
		
	});  

Now we can test our api and backbone collection in our browser:

.. code-block:: javascript

	> var c = new JULY.CommitCollection(null,{projectId: 1});
	> c.total
	0
	> c.fetch()
	> c.total
	649
	> c.models.length
	20
	> c.models
	[child, child,...]
	> c.models[0].get('hash')
	"347f32a946d41b59ea3f8b3dad07f73f4593d1e7"
	> c.models[0].get('message')
	"This is a fancy commit message!"
	> c.fetch({add: true}) // add=true will append the new models
	> c.models.length
	40

This just scratches the surface of what you can do with Backbonejs_. As 
you can see with very little code we already have an api and a client library
to read it. Now we just need to display the commits to the user. You could 
do this with Backbone and it would probably work just fine. However I find
that Backbone views just end up being a bunch of boiler plate logic and they
have to be manually sync'd up. 

Knockout and Knockback
-----------------------

Knockoutjs_ is a declarative binding UI library that applies the 
`Model-View-View Model`_ (MVVM) pattern. It provides dependancy tracking and
Automatic UI refresh. It is really great as it handles nearly every UI
interaction you would expect plus has a customizable binding system to 
cover all the other use cases. 

There are a number of built in bindings, here are the main ones we'll use:

* foreach: loops over an list of item and duplicates a section of markup
* text: Replaces the text of the element with the attribute value
* attr: Replaces the attributes of an element 
* visible: If the value is true shows the element

Here is what our commit list looks like:

.. code-block:: html

	<div id="commits">
	  <div data-bind="foreach: commits">
  		<div class="media">
    	  <img class="media-object" data-bind="attr: {src: url, alt: message}" />
    	  <div class="media-body">
    	  	<h4 class="media-heading" data-bind="text: timestamp"></h4>
    		<strong data-bind="text: message"></strong>
    		<p class="hash">
              	<a data-bind="visible: url, attr:{href:url }">
              	  <span data-bind="text: hash"></span>
              	</a>
                <!-- attributes are functions, 
                     so to check the negative you have to call it -->
                <span data-bind="visible: !url(), text: hash"></span>
              </p>
      	  </div>
        </div>
  	</div>
  	<script>
  	  <!-- simple example of view binding -->
  	  var view = {
  	     commits: ko.observableArray([
		    { url: "/foo/", timestamp: "12-02-2012", message: "Foo" },
		    { url: "/bar/", timestamp: "12-02-2012", message: "Bar" },
		    { url: "/bean/", timestamp: "12-02-2012", message: "Beans" }
		]);
	  }
	  ko.applyBindings(view);
	</script>

The beauty of the declarative binding is that you can separate all the logic
from you models and the views that display them. This is alot like the MVC
pattern Django and other frameworks preach.

The major downside to using Knockoutjs_ is that it does next to nothing with
your REST-ful urls. That exercise if left up to the user. Which is where
Knockbackjs_ comes in. 

Knockbackjs_ as its name suggests glues Knockoutjs_ and Backbonejs_ together.
With Knockbackjs_ you can use the powerful ORM that backbone provides with
the automatically updating UI of Knockoutjs_. Knockback provides a few functions
to assist in creating your view and automatically wraps the Backbone models
or collections in Knockout obverables.

Since we like the Backbonejs_ method of extending we first mimic it. This 
allows us to have a initialize method in our view models:

.. code-block:: javascript

	JULY.ViewModel = function(options) {
		this.initialize.apply(this,arguments);
	};
	_.extend(JULY.ViewModel.prototype, {
		initialize: function() {}
	});
	JULY.ViewModel.extend=Backbone.View.extend;

.. note:: Knockbackjs_ views are just standard Javascript objects.
	
Now lets create a view for our commits:

.. code-block:: javascript

	JULY.CommitsView = JULY.ViewModel.extend({
		
		initialize: function(options) {
		    var c = new JULY.CommitCollection(null, options);
		    // prepopulate the collection
		    c.fetch({add: true});
		    this.commits = kb.collectionObservable(c);
		},

		// bind this function to the parent div and when 
		// the element is scrolled call the fetch method when
		// we are near the bottom.
		// http://jsfiddle.net/rniemeyer/KdPmF/
		scrolled: function(data, event) {
	        var elem = event.target;
	        if (elem.scrollTop > (elem.scrollHeight - elem.offsetHeight - 200)) {
	            this.fetch();
	        }
	    },
	    
	    // Check the collection to see if there are more commits to fetch
	    hasMore: function() {
	    	return this.commits.collection().hasMore;
	    }, 
	    	
	    // Fetch more commits from the collection
		fetch: function() {
		    if (this.hasMore()) {
		    	this.commits.collection().fetch({add:true});
		    }
		}
	});

Thats it, now we just need to bind this in our template logic.

.. code-block:: html

	<div id="commits">
	  <div data-bind="foreach: commits, event: { scroll: scrolled }">
	     
	     <!-- the rest is copied from above -->
	  
	  </div>
	</div>
	
	<script type="text/javascript">
	    // {{ project.id }} is populated by Django in our view logic
	    var view = new JULY.CommitsView({projectId: {{ project.id }}});
	    ko.applyBindings(view);
	</script>

Custom Bindings
~~~~~~~~~~~~~~~

Now we just need to make one minor improvement, lets make our dates fancy 
with a jQuery plugin timeago_. We could just use it on the page in the script
tag but lets do it the proper way with a custom binding.

.. code-block:: javascript

	ko.bindingHandlers.timeago = {
	    init: function(element, valueAccessor, allBindingsAccessor) {
	        // First get the latest data that we're bound to
	        var value = valueAccessor(), allBindings = allBindingsAccessor();
	     
	        // Next, whether or not the supplied model property is observable, 
	        // get its current value
	        var valueUnwrapped = ko.utils.unwrapObservable(value);
	        
	        // set the title attribute to the value passed
	        $(element).attr('title', valueUnwrapped);
	        
	        // apply timeago to change the text of the element
	        $(element).timeago();
	    }
	};

Now we apply our custom binding in the html like this:

.. code-block:: html

	<h4 class="media-heading" data-bind="timeago: timestamp"></h4>

Wrap Up
-------


.. _j(an)ulython: http://www.julython.org
.. _backbonejs: http://backbonejs.org
.. _tastypie: http://django-tastypie.readthedocs.org/en/latest/toc.html
.. _knockoutjs: http://knockoutjs.com/
.. _knockbackjs: http://kmalakoff.github.com/knockback/
.. _backbone-tastypie: https://github.com/PaulUithol/backbone-tastypie
.. _timeago: http://timeago.yarp.com/
.. _model-view-view model: http://knockoutjs.com/documentation/observables.html#mvvm_and_view_models