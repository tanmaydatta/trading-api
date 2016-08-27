from django.conf.urls import url

from views import *

urlpatterns = [
    # url(r'^$', test, name='test'),
    url(r'^test/$', test, name='test'),
    url(r'^home/$', home, name='home'),
    url(r'^home/(?P<strategy>.+)/$', home_st, name='home_st'),
    url(r'^stop/(?P<symbol>.+)/$', stop, name='stop'),
    url(r'^flat/(?P<symbol>.+)/$', flat, name='flat'),
    url(r'^stop_all/$', stop_all, name='stop_all'),
    url(r'^running/$', running, name='running'),
    url(r'^search/(?P<symbol>.+)/$', search, name='search'),
    url(r'^set_request/$', set_request, name='set_request'),
    url(r'^set_access/$', set_access, name='set_access'),
    url(r'^check_connection/$', check_connection, name='check_connection'),
    url(r'^cancel/(?P<ins_token>.+)/$', cancel, name='cancel'),
]
