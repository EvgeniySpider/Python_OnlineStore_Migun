from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from goods.models import Product
from users.forms import CustomUserCreationForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView


class IndexView(ListView):
    model = Product
    template_name = 'index.html'
    context_object_name = 'products'  # Имя переменной в шаблоне


class SignUpView(UserPassesTestMixin, CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'users/register.html'

    def test_func(self):
        # Доступ разрешен ТОЛЬКО анонимным пользователям (неавторизованным)
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        # Если пользователь УЖЕ залогинен — кидаем его на главную страницу
        return redirect('home')


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True  # Если юзер УЖЕ залогинен, не пускаем его на форму входа

    def get_success_url(self):
        return reverse_lazy('home')  # Куда отправить после успешного входа