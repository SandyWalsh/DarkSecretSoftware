from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'dss.pizza.views.welcome', name='welcome'),
    url(r'^order/$', 'dss.pizza.views.order', name='order'),
)
