from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.db import transaction
from .forms import OrderModelForm



class OrderCreateView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user

        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'city': user.city,
            'street': user.street,
            'house_number': user.house_number,
            'apartment_number': user.apartment_number,
        }

        form = OrderModelForm(initial=initial_data)
        context = {
            'form':form
        }
        return render(request, 'orders/order_create.html', context)

    @method_decorator(transaction.atomic)
    def post(self, request, *args, **kwargs):
        form = OrderModelForm(data=request.POST)
        

