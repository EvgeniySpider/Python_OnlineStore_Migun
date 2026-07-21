
from django.urls import path
from users.views import SignUpView

urlpatterns = [
    path('register/', SignUpView.as_view(), name='register'),
    
]
