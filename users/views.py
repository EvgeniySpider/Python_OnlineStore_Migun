from django.views import View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from users.forms import CustomUserCreationForm, UserDataForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView
from orders.models import Order


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


class UserDataView(LoginRequiredMixin, View):
    def get(self, request):
        form = UserDataForm(instance=request.user)
        orders = Order.objects.filter(user=request.user).prefetch_related('items')
        context = {
            'form': form,
            'orders':orders,
        }
        return render(request, 'users/user_data_and_orders.html', context)

    def post(self, request):
        # Передаем и данные из формы, и экземпляр, который надо обновить
        form = UserDataForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('user_profile')
        
        return render(request, 'users/user_data_and_orders.html', {'form': form})