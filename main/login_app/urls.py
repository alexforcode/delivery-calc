from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = 'login'

urlpatterns = [
    path('',
         auth_views.LoginView.as_view(template_name='login/login.html', redirect_authenticated_user=True),
         name='login'),
    path('logout/',
         views.CustomLogoutView.as_view(),
         {'next_page': settings.LOGOUT_REDIRECT_URL},
         name='logout'),
]