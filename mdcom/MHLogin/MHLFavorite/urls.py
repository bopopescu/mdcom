#-*- coding: utf-8 -*-
'''
Created on 2013-5-28

@author: xwin
'''
try:
	from django.conf.urls import patterns
except ImportError:  # remove when django 1.5 fully integrated
	from django.conf.urls.defaults import patterns

urlpatterns = patterns('MHLogin.MHLFavorite',
	(r'^$', 'views.my_favorite'),
	(r'^Toggle/$', 'views.toggle_favorite'),
)