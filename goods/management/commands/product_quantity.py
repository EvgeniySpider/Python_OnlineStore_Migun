from django.core.management.base import BaseCommand, CommandError
from goods.models import Product, Stock
from django.db.models import F

class Command(BaseCommand):
    help = 'Изменение количества товара на складе'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['increase', 'decrease'],
            help='Действие: increase — увеличить количество, decrease — уменьшить количество',
        )
        parser.add_argument(
            'product_name',
            type=str,
            help='Название товара, если в названии товара есть пробел/ы то нужно обрамить его в кавычки',
        )
        parser.add_argument(
            'quantity',
            type=int,
            help='Количество единиц для добавления/уменьшения',
        )

    def handle(self, *args, **options):
        action = options['action']
        product_name = options['product_name'].replace('_', ' ')
        quantity = options['quantity']

        if quantity <= 0:
            raise CommandError('Количество не может быть нулём или отрицательным числом')

        try:
            product = Product.objects.get(name=product_name)
        except Product.DoesNotExist:
            raise CommandError(f'Товар "{product_name}" не найден в базе данных.')

        try:
            stock = Stock.objects.get(product=product)
        except Stock.DoesNotExist:
            raise CommandError(
                f'Остаток для товара "{product_name}" не найден в базе данных.'
            )

        if action == 'increase':
            stock.quantity = F('quantity') + quantity
            stock.save(update_fields=['quantity'])

        elif action == 'decrease':
            if stock.quantity < quantity:
                raise CommandError(f'Количество отнимаемого товара "{product_name}" не может быть больше его наличия'
                                   f' \n{stock.quantity} < {quantity}')
                
            stock.quantity = F('quantity') - quantity
            stock.save(update_fields=['quantity'])

        word, style = ('увеличено', self.style.SUCCESS) if action == 'increase' \
                 else ('уменьшено', self.style.ERROR)


        self.stdout.write(
            style(
                f'Количество товара "{product.name}" {word} на {quantity} шт. '
                f'Текущий остаток: {stock.quantity} шт.'
            )
        )
