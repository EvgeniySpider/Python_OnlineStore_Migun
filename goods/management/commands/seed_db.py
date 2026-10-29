from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError

from goods.models import Category, Product, Stock


class Command(BaseCommand):
    help = "Наполняет базу данных начальными тестовыми данными (категории, товары, остатки)"

    def handle(self, *args, **options):
        categories_data = [
            "Электроника",
            "Бытовая химия",
            "Лекарственные препараты",
            "Пищевые продукты",
        ]

        products_data = [
            # Электроника
            {
                "name": "Ноутбук MSI GF63",
                "desc": "Игровой ноутбук RTX 3050, Core i5, 16GB RAM",
                "price": 75000.00,
                "cat": "Электроника",
                "qty": 10,
            },
            {
                "name": "Смартфон Xiaomi Redmi Note 13",
                "desc": '6.67" AMOLED 120Гц, 8/256 ГБ',
                "price": 21990.00,
                "cat": "Электроника",
                "qty": 7,
            },
            {
                "name": "Беспроводные наушники Sony WH-1000XM5",
                "desc": "Шумоподавление, до 30 часов работы",
                "price": 34990.00,
                "cat": "Электроника",
                "qty": 5,
            },
            {
                "name": 'Монитор LG UltraGear 27"',
                "desc": "IPS, 144Hz, 1ms, Full HD",
                "price": 22500.00,
                "cat": "Электроника",
                "qty": 12,
            },
            # Бытовая химия
            {
                "name": "Дегтярное мыло",
                "desc": "Традиционное мыло с натуральным берёзовым дёгтем",
                "price": 65.00,
                "cat": "Бытовая химия",
                "qty": 45,
                "image": "products/tar_soap.png",
            },
            {
                "name": "Хозяйственное мыло 72%",
                "desc": "Классическое твердое мыло, 200г",
                "price": 45.00,
                "cat": "Бытовая химия",
                "qty": 12,
            },
            {
                "name": "Гель для стирки Ariel 3л",
                "desc": "Универсальный концентрат для белого и цветного",
                "price": 1290.00,
                "cat": "Бытовая химия",
                "qty": 12,
            },
            {
                "name": "Дезодорант Axe Dark Temptation",
                "desc": "Мужской аэрозоль, 150 мл",
                "price": 380.00,
                "cat": "Бытовая химия",
                "qty": 20,
            },
            # Лекарственные препараты
            {
                "name": "Капли глазные Данцил",
                "desc": "Антибактериальное средство 0.3%, 5 мл",
                "price": 185.00,
                "cat": "Лекарственные препараты",
                "qty": 3,
            },
            {
                "name": "Перцовый баллончик Шпага 65мл",
                "desc": "Струйно-аэрозольный тип распыления",
                "price": 650.00,
                "cat": "Лекарственные препараты",
                "qty": 15,
            },
            {
                "name": "Ибупрофен 400мг",
                "desc": "Обезболивающее и жаропонижающее, 20 таб.",
                "price": 120.00,
                "cat": "Лекарственные препараты",
                "qty": 12,
            },
            {
                "name": "Спрей для носа Аква Марис",
                "desc": "Натуральная морская вода для промывания",
                "price": 420.00,
                "cat": "Лекарственные препараты",
                "qty": 12,
            },
            # Пищевые продукты
            {
                "name": "Лапша Доширак (Говядина)",
                "desc": "Лапша быстрого приготовления, острый вкус",
                "price": 70.00,
                "cat": "Пищевые продукты",
                "qty": 100,
            },
            {
                "name": "Энергетический напиток Red Bull 0.25л",
                "desc": "Бодрящий напиток",
                "price": 160.00,
                "cat": "Пищевые продукты",
                "qty": 12,
            },
            {
                "name": "Шоколад Ritter Sport с фундуком",
                "desc": "Молочный шоколад, 100г",
                "price": 145.00,
                "cat": "Пищевые продукты",
                "qty": 12,
            },
            {
                "name": "Чай зелёный Greenfield Flying Dragon",
                "desc": "100 пакетиков в фольгированных конвертах",
                "price": 390.00,
                "cat": "Пищевые продукты",
                "qty": 12,
                "image": "products/greenfield_flying_dragon_100_teabags.png",
            },
        ]

        try:
            # Оборачиваем всё в транзакцию: если что-то упадёт, база откатится к начальному состоянию
            with transaction.atomic():
                self.stdout.write("Создание категорий...")
                category_objects = {}
                for cat_name in categories_data:
                    cat_obj, created = Category.objects.get_or_create(name=cat_name)
                    category_objects[cat_name] = cat_obj
                    if created:
                        self.stdout.write(f'  + Категория "{cat_name}" добавлена')

                self.stdout.write("\nСоздание товаров и остатков на складе...")
                for item in products_data:
                    # Создаём или получаем товар (ищем по имени, чтобы не дублировать)
                    product, created = Product.objects.get_or_create(
                        name=item["name"],
                        defaults={
                            "description": item["desc"],
                            "price": item["price"],
                            "category": category_objects[item["cat"]],
                            "image": item.get("image", ""),
                        },
                    )

                    # Обновляем или создаём остаток на складе
                    Stock.objects.update_or_create(
                        product=product, defaults={"quantity": item["qty"]}
                    )

                    if created:
                        self.stdout.write(
                            f'  + Товар "{product.name}" добавлен ({item["qty"]} шт.)'
                        )
                    else:
                        self.stdout.write(
                            f'  ~ Товар "{product.name}" уже существует (остаток обновлён до {item["qty"]} шт.)'
                        )

            self.stdout.write(
                self.style.SUCCESS("\nБаза данных успешно наполнена тестовыми данными!")
            )

        # Перехватываем ошибки отсутствия таблиц (если забыли сделать migrate)
        except (OperationalError, ProgrammingError) as e:
            self.stderr.write(
                self.style.ERROR(
                    "\nОшибка БД: Таблицы не найдены. Вы забыли применить миграции?\n"
                    "Выполните команду: poetry run python manage.py migrate"
                )
            )
            self.stderr.write(f"Детали ошибки: {e}")
