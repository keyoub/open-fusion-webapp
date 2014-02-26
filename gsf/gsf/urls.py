from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'gsf.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^oauth2/', include('provider.oauth2.urls', namespace = 'oauth2')),
    url(r'^show/', include('show.urls')),
    url(r'^api/', include('api.urls')),
    #url(r'^admin/', include(admin.site.urls)),
)
