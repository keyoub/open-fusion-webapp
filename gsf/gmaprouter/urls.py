from django.conf.urls import patterns, url

from gmaprouter import views

urlpatterns = patterns('', 
	# ex: /show/
	url(r'^$', views.index, name='index'),
)

