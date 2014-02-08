from django.conf.urls import patterns, url

from show import views

urlpatterns = patterns('', 
	# ex: /show/
	url(r'^$', views.index, name='index'),
	url(r'^insert/$', views.insert, name='insert'),
)

