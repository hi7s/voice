#!/usr/bin/env python
from django.conf.urls import *

from blog import views
from feeds import ArticlesFeed, CommentsFeed

urlpatterns = [
    url(r'^$', views.latest),
    url(r'^article/(\d+)/$', views.article),
    url(r'^category/(\S+)/$', views.category),
    url(r'^page/(\S+)/$', views.page),
    url(r'^latest/$', views.latest),
    url(r'^random/$', views.random),
    url(r'^tag/(\S+)/$', views.tag),
    url(r'^favorite/$', views.favorite),
    url(r'^archive/$', views.archive),
    url(r'^archive/(\d{4})/$', views.archive_by_year),
    url(r'^archive/(\d{4})/(\d{1,2})/$', views.archive_by_month),
    url(r'^search/$', views.search),
    url(r'^feeds/rss2$', ArticlesFeed()),
    url(r'^feeds/comments-rss2$', CommentsFeed()),
    url(r'^feeds/(?P<str>\S+)$', views.feed),
]
