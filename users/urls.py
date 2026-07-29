
from django.urls import path
from users.views import CustomLoginView, SignUpView, UserDataView
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('register/', SignUpView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserDataView.as_view(), name='user_profile')
]
