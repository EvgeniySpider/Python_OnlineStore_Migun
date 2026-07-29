from django.views import View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from users.forms import CustomUserCreationForm, UserDataForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView


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
        user = request.user

        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'patronymic':user.patronymic,
            'email':user.email,
            'phone_number': user.phone_number,
            'city': user.city,
            'street': user.street,
            'house_number': user.house_number,
            'apartment_number': user.apartment_number,
        }

        form = UserDataForm(initial=initial_data)
        context = {
            'form': form
        }

        return render(request, 'users/user_data_and_orders.html', context)

    def post(self, request):
        pass