import json
from django.core.management.base import BaseCommand
from django.db import models
from goods.models import Product, Stock


class Command(BaseCommand):
    help = 'Экспорт остатков товаров в JSON-файл'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='residue.json',
            help='Имя файла для сохранения остатков',
        )

    def handle(self, *args, **options):
        # Извлекаем распарсенный аргумент из словаря options
        file_path = options['file']
        
        raw_data = list(Product.objects.values(
            'name', 
            quantity=models.F('stock__quantity') # Переименовываем stock__quantity в quantity
        ))

        # Сохраняем прямо в файл
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=4)

        self.stdout.write(
            self.style.SUCCESS(f'Остатки успешно выгружены в {file_path}')
        )