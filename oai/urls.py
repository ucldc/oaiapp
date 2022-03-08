from django.conf.urls import url
from . import views

app_name = 'oai'
urlpatterns = [
    url(r'^(?P<repo_id>[-\w]+)/$', views.oai, name='oai'),
    url(r'', views.list_repositories, name='list_repositories'),
]
