
from django.urls import path
from users.views import CustomLoginView, SignUpView

urlpatterns = [
    path('register/', SignUpView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
