from django.conf.urls import patterns, url
from user_profiles import views

urlpatterns = patterns('',
    url(r'^$', views.index, name = 'index'),
    url(r'^(?P<user_name>\w+)/$', views.view, name = 'view'),
    #url(r'^(?P<lesson_id>\d+)/question/$', views.question, name = 'question'),

)
