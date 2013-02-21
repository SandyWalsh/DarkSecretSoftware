from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'dss.website.views.home', name='home'),
    url(r'query/', 'dss.website.views.query', name='query'),
    url(r'reset/', 'dss.website.views.start_over', name='reset'),
    url(r'card', 'dss.website.views.card', name='card'),
    url(r'card/', 'dss.website.views.card', name='card'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
