import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class UserDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'patronymic',
            'email',
            'phone_number',
            'city',
            'street',
            'house_number',
            'apartment_number'
        )
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            return phone
        
        # Разрешаем формат: опциональный плюс в начале и от 7 до 15 цифр
        # (или можно очистить от скобок/пробелов/дефисов)
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Проверяем, что остались только цифры (и возможный + в начале)
        if not re.fullmatch(r'^\+?\d{7,15}$', cleaned_phone):
            raise ValidationError('Номер телефона должен содержать только цифры (допускается "+" в начале).')
            
        return cleaned_phone

    def clean_apartment_number(self):
        apartment = self.cleaned_data.get('apartment_number')
        # Если поле пустое (оно ведь необязательное blank=True), пропускаем
        if not apartment:
            return apartment

        # Если введено — проверяем строго на цифры
        if not str(apartment).strip().isdigit():
            raise ValidationError('Номер квартиры/офиса должен состоять только из цифр.')

        return apartment.strip()
