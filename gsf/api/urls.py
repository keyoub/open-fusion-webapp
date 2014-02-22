from django.conf.urls import patterns, url

from api import views

urlpatterns = patterns('', 
	# ex: /show/
	#url(r'^$', views.index, name='index'),
	url(r'^upload/$', views.upload, name='upload'),
	url(r'^download/$', views.download, name='download'),
)

