Julython Code Refresh
=================================

:author: Robert Myers
:date: 2012-12-24 20:12
:category: Code
:tags: python, opensource
:style: participating
:summary: Julython is now running on Rackspace

When we launched over 6 months ago the site was built on `Google Appengine`_. 
The site was built with Django_ but used the builtin datastore_ for models. 
`Google Appengine`_ provides a complete set of tools to run any web application.
Running on a PAAS_ removes a lot of the headaches associated with running a 
production site.   

Then last month I started a new job at Rackspace_ working on the 
`Cloud Database`_ product which is `open source`_. It is really great to work
for a company that recognizes the power of open source. Naturally I have to dog 
food my own product, that and they are footing the bill :) So I got to work on
converting the site to use standard Django_ models, Tastypie_, `Django Social
Auth`_, and South_. I am quite pleased with the results. Ironically the site 
now takes advantange of more open source projects, which we are trying to 
promote :)

Architechture
-------------

.. warning:: I work for Rackspace_ 'insert standard disclaimer here'. 

The new site uses a couple of products from the cloud services at Rackspace_.
First there is a `Cloud Load Balancer`_ in front of two 512 MB `Cloud Servers`_. 
The two web nodes are running a nginx_ proxy in front of gunicorn_. The web
nodes talk to a 512 MB MySQL `Cloud Database`_.

Appengine has a great tool for `monitoring performance`_ of your web apps. The 
dashboard has a number of graphs as well to check on the health of your web
app. This is hard to give up, which is why I turned to `New Relic`_. With 
`New Relic`_ you get much_ more_ data_, I do not regret the switch. (well, it
costs money but still, it is worth it)

<shameless plug>

During `J(an)ulython`_ I'll be working on my project cannula_ which is a 
deployment tool for websites. Using cannula_ I can deploy the site like so::

	$ git push cannula master

</shameless plug>

Living on the Edge
------------------

Even though Django 1.5 is still in beta it is worth running to get 
the new `configurable User model`_. This made the transition super easy from 
webapp2_ user models on Appengine to a 
custom class to interact with `Django Social Auth`_ properly. Webapp2_ stores the
auth_ids in the format 'provider:uid' in a list property on the User class. It 
also provides methods to add new auth ids etc. Now with Django 1.5 you can alter
the User Class to add custom fields or methods. Here is the User model from
Julthon:

.. code-block:: python
	
	from django.db import models
	from django.contrib.auth.models import AbstractUser
	from social_auth.models import UserSocialAuth

	class User(AbstractUser):
	    description = models.TextField(blank=True)
	    url = models.URLField(blank=True, null=True)
	    # more custom fields here
	
	    def add_auth_id(self, auth_str):
	        """
	        Example::
	            user = User.objects.get(username='foo')
	            user.add_auth_id('email:foo@example.com')
	        """
	        provider, uid = auth_str.split(':')
	        UserSocialAuth.create_social_auth(self, uid, provider)
	    
	    @classmethod
	    def get_by_auth_id(cls, auth_str):
	        """
	        Example::
	            user = User.get_by_auth_id('twitter:julython')
	        """
	        provider, uid = auth_str.split(':')
	        sa = UserSocialAuth.get_social_auth(provider, uid)
	        if sa is None:
	            return None
	        return sa.user
	
	    @property
	    def auth_ids(self):
	        auths = self.social_auth.all()
	        return [':'.join([a.provider, a.uid]) for a in auths]

.. note:: Using the provider 'email' you can store multiple email addresses for 
	the user and let `Django Social Auth`_ handle the uniqueness of email 
	addresses.

Now with very little change to the api endpoint for commits it is easy to
associate a commit with a user by email address.

.. code-block:: python

	class Commit(models.Model):
	    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
	    hash = models.CharField(max_length=255, unique=True)
	    author = models.CharField(max_length=255, blank=True)
	    name = models.CharField(max_length=255, blank=True)
	    email = models.CharField(max_length=255, blank=True)
	    message = models.CharField(max_length=2024, blank=True)

	    @classmethod
	    def user_model(cls):
	    	"""No need to import our custom user model."""
	        return cls._meta.get_field('user').rel.to
	    
	    @classmethod
	    def create_by_email(cls, email, commits, project=None):
	        """Create a commit by email address"""
	        user = cls.user_model().get_by_auth_id('email:%s' % email)
			# create the commit here
	        
You could accomplish everything just by interacting with `Django Social Auth`_ 
models. It just seems a little cleaner to use methods on the User model to 
get a user or add properties to it. The commit model in this case really should
not care about the Social Auth models.


SQL Oh How I Missed You
-----------------------

I love NoSQL, I hate altering tables. It is even better with Appengine as the
datastore is just there, zero configuration and no syncing tables. It's a lazy
developers dream come true. My biggest complaints of the Datastore is the
lack of a (fast and complete) `count method`_ and if you want to do a query 
there has to be an `Index built for it`_. Some things are just easier to do 
with SQL. 

Location and Team Totals
~~~~~~~~~~~~~~~~~~~~~~~~

One major pain point with the code during July was when people changed
their location or team. Since all of the data was denormalized_ this meant that 
both location or team totals needed to be updated. Appengine has a nice builtin 
`deferred task`_ tool to spawn background tasks to do this. But in the SQL 
world this is just a simple JOIN query. Okay it is slightly complex, but still 
easy to pull off with a `raw query`_. 

First here is the Location model:

.. code-block:: python

	class Location(models.Model):
	    slug = models.SlugField(primary_key=True)
	    name = models.CharField(max_length=64, blank=False)
	    total = models.IntegerField(default=0) # this field is never updated!

The total field is never actually updated it is just there to have a property
to display the total from the raw query. If you have never used a `raw
query`_ this is a great use case for it. Raw queries allow you to run
any custom SQL and return the Model objects. In this example the total for any
one location is the sum of all the people in that location. Here is what that 
looks like in SQL:

.. code-block:: sql

	SELECT july_user.location_id AS slug,
	    people_location.name AS name,
	    SUM(game_player.points) AS total 
	    FROM game_player, july_user, people_location 
	    WHERE game_player.user_id = july_user.id
	    AND july_user.location_id = people_location.slug 
	    AND game_player.game_id = %s
	    GROUP BY july_user.location_id 
	    ORDER BY total DESC
	    LIMIT 50;

The magic is all in the "GROUP BY" statement. This SQL
takes all the players (people who commited during the month) groups them by
their location and sums up all their scores. Also you will notice it's returning
the fields ('slug', 'name', 'total') which are the same fields on the Location 
model. All it needs is the game id and it will return the top 50 locations:

.. code-block:: python

	>>> query = Location.objects.raw(LOCATION_SQL, [1])
	>>> locations = [l for l in query]
	>>> print locations
	[<Location: Atlanta, GA>,
	 <Location: Philadelphia, PA>,
	 <Location: Boston, MA, USA>,
	 <Location: Austin, TX>,
	 ...
	
	>>> atl = locations[0]
	>>> print atl.name
	Atlanta, GA
	>>> print atl.total
	1625

.. warning:: I you plan on using raw queries be sure *not* to use string
    formatting on the SQL. This will protect you from `SQL injection attacks`_.

This is cleaner and more exact in comparison to the old code. Now
the locations and teams are up to date without a `deferred task`_ or other
background tasks. Normalization_ FTW!

Migrations
~~~~~~~~~~

The Datastore_ on `Google Appengine`_ like other NoSQL_ databases does not
require any schema modifications or table creation staments. This is great for
development as you can freely change your data models or add new ones without
any errors or extra work. Tranditional `relational databases`_ require a bit
more hand holding. If you haven't heard it yet you should use South_ to manage
migrations. On top of managing the standard `alter table`_ statements it also
provides support for `data migrations`_ as well.

Wrap up
-------

Moving away from a complete PAAS_ solution can be a little scary. Thankfully
there are a number of projects that can help your transition. I plan on
detailing other aspects of the site in this blog as well. Hit the comment
section up if you have any questions!





.. _j(an)ulython: http://www.julython.org
.. _google appengine: https://developers.google.com/appengine/
.. _rackspace: http://www.rackspace.com
.. _cloud database: http://www.rackspace.com/cloud/public/databases/
.. _cloud load balancer: http://www.rackspace.com/cloud/public/loadbalancers/
.. _cloud servers: http://www.rackspace.com/cloud/public/servers/
.. _open source: https://github.com/stackforge/reddwarf
.. _django: http://djangoproject.org
.. _tastypie: http://django-tastypie.readthedocs.org/en/latest/tutorial.html
.. _django social auth: http://django-social-auth.readthedocs.org/en/latest/
.. _south: http://south.readthedocs.org/en/0.7.6/
.. _webapp2: http://webapp-improved.appspot.com/
.. _nginx: http://wiki.nginx.org/Main
.. _gunicorn: http://gunicorn.org
.. _cannula: https://github.com/rmyers/cannula
.. _count method: https://developers.google.com/appengine/docs/python/datastore/queryclass#Query_count
.. _index built for it: https://developers.google.com/appengine/docs/python/datastore/indexes
.. _monitoring performance: https://developers.google.com/appengine/docs/python/tools/appstats
.. _new relic: http://newrelic.com
.. _much: https://newrelic.com/product/real-user-monitoring
.. _more: https://newrelic.com/product/application-monitoring
.. _data: https://newrelic.com/product/server-monitoring
.. _configurable user model: https://docs.djangoproject.com/en/dev/topics/auth/#auth-custom-user
.. _normalization: http://en.wikipedia.org/wiki/Database_normalization
.. _denormalized: http://en.wikipedia.org/wiki/Denormalization
.. _deferred task: https://developers.google.com/appengine/articles/deferred
.. _raw query: https://docs.djangoproject.com/en/dev/topics/db/sql/
.. _sql injection attacks: https://docs.djangoproject.com/en/dev/topics/db/sql/#passing-parameters-into-raw
.. _datastore: https://developers.google.com/appengine/docs/python/datastore/overview
.. _nosql: http://en.wikipedia.org/wiki/NoSQL
.. _relational databases: http://en.wikipedia.org/wiki/Relational_database
.. _alter table: http://south.readthedocs.org/en/0.7.6/tutorial/part1.html#changing-the-model
.. _data migrations: http://south.readthedocs.org/en/0.7.6/tutorial/part3.html#data-migrations
.. _paas: http://en.wikipedia.org/wiki/Platform_as_a_service
