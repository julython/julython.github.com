#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = u"Robert Myers"
SITENAME = u"Julython Blog"
SITEURL = 'http://blog.julython.org'
THEME = '.'
TIMEZONE = 'America/Chicago'

GITHUB_URL = 'https://github.com/julython/julython.org'
DEFAULT_LANG = 'en'

# Blogroll
#LINKS =  (('Pelican', 'http://docs.notmyidea.org/alexis/pelican/'),
#          ('Python.org', 'http://python.org'),
#          ('Jinja2', 'http://jinja.pocoo.org'),
#          ('You can modify those links in your config file', '#'),)

# Social widget
#SOCIAL = (('You can add links in your config file', '#'),
#          ('Another social link', '#'),)

DEFAULT_PAGINATION = 10
ARTICLE_URL ='{date:%Y}/{date:%b}/{slug}/'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%b}/{slug}/index.html'

TWITTER_USERNAME = 'julython'
DISQUS_SITENAME = 'julythonblog'
GOOGLE_ANALYTICS = 'UA-31203363-2'

MENUITEMS = (('Talks', '/talks/'),)
