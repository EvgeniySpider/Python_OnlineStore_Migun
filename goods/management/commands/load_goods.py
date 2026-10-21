import json
from django.core.management.base import BaseCommand
from goods.models import Product, Stock


class Command(BaseCommand):
    help = 'Импорт остатков товаров из JSON-файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='residue.json',
            help='Имя файла для импорта остатков',
        )

    def handle(self, *args, **options):
        def _message(product, stock, created):
            if created:
                return f'Товар "{product.name}" был успешно добавлен. Количество: {stock.quantity} шт.'
            return f'Количество товара "{product.name}" успешно обновлено и теперь составляет {stock.quantity} шт.'

        file_path = options['file']

        with open(file_path, 'r', encoding='UTF-8') as f:
            data = json.load(f)

        for string in data:
            try:
                product = Product.objects.get(name=string['name'])
                stock, created = Stock.objects.update_or_create(
                    product=product,
                    defaults={'quantity': string['quantity']}
                )
                
                style = self.style.SUCCESS if created else self.style.WARNING
                self.stdout.write(style(_message(product, stock, created)))

            except Product.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f"Товар '{string['name']}' не найден в базе данных!")
                )

        self.stdout.write(
            self.style.SUCCESS(f'Остатки в таблице {Stock._meta.db_table} успешно обновлены')
        )