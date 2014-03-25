from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from home import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', include('home.urls')),
    url(r'^about/$', 
         TemplateView.as_view(template_name='home/about.html'), name="home"),
    url(r'^show/', include('show.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
