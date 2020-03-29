from django.urls import path
from django.conf.urls import url

from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path('scrape/', views.scrape, name="scrape"),
    path('', RedirectView.as_view(url='/home')),
    path('home/',  views.home, name="home"),
    path('blog/', views.blog, name="blog"),
    path('contact/', views.contact, name="contact"),
    path('test/', views.test, name="test"),

]