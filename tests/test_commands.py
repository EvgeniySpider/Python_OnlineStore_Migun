import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

from goods.models import Product, Stock


@pytest.mark.django_db
@pytest.mark.parametrize(
    "action, change_quantity, expected_quantity, expected_word",
    [
        ("increase", 5, 15, "увеличено на 5 шт."),  # Было 10 + 5 = 15
        ("decrease", 4, 6, "уменьшено на 4 шт."),  # Было 10 - 4 = 6
    ],
)
def test_product_quantity_success(
    action: str,
    change_quantity: int,
    expected_quantity: int,
    expected_word: str,
    product: Product,
    stock: Stock,
):
    """Успешное увеличение и уменьшение количества товара на складе через management-команду."""
    assert stock.quantity == 10

    # Проверяем замену символа '_' на пробел ('Ноутбук_MSI' -> 'Ноутбук MSI')
    product_name_arg = product.name.replace(" ", "_")
    out = StringIO()

    # Вызываем management-команду
    call_command(
        "product_quantity", action, product_name_arg, change_quantity, stdout=out
    )

    # Обновляем инстанс из базы (так как во вьюхе используется F-выражение)
    stock.refresh_from_db()

    # 1. Проверяем остаток в БД
    assert stock.quantity == expected_quantity

    # 2. Проверяем вывод команды в консоли (stdout)
    output = out.getvalue()
    assert expected_word in output
    assert f"Текущий остаток: {expected_quantity} шт." in output


@pytest.mark.django_db
class TestCommandProductQuantityNegative:
    @pytest.mark.parametrize("action", ("increase", "decrease"))
    def test_product_when_quantity_zero_or_negative(
        self, action: str, product: Product, stock: Stock
    ):
        """Попытка передать количество 0 или отрицательное число."""
        assert stock.quantity == 10

        with pytest.raises(CommandError) as exc_info:
            call_command("product_quantity", action, product.name, 0)

        assert "Количество не может быть нулём или отрицательным числом" in str(
            exc_info.value
        )
        stock.refresh_from_db()
        assert stock.quantity == 10

    @pytest.mark.parametrize("action", ("increase", "decrease"))
    def test_product_when_product_doesnt_exist(self, action: str, stock: Stock):
        """Попытка изменить количество несуществующего товара."""
        assert stock.quantity == 10

        with pytest.raises(CommandError) as exc_info:
            call_command("product_quantity", action, "клей", 2)

        assert 'Товар "клей" не найден в базе данных.' in str(exc_info.value)
        stock.refresh_from_db()
        assert stock.quantity == 10

    @pytest.mark.parametrize("action", ("increase", "decrease"))
    def test_product_when_stock_doesnt_exist(self, action: str, product: Product):
        """Попытка изменить количество, если у товара нет записи на складе."""
        product.stock.delete()

        with pytest.raises(CommandError) as exc_info:
            call_command("product_quantity", action, product.name, 2)

        assert f'Остаток для товара "{product.name}" не найден в базе данных.' in str(
            exc_info.value
        )
        assert not Stock.objects.filter(product=product).exists()

    def test_product_when_decrease_goods_quantity_less_than_have(
        self, product: Product, stock: Stock
    ):
        """Попытка списать больше товара, чем есть на складе."""
        assert stock.quantity == 10

        with pytest.raises(CommandError) as exc_info:
            call_command("product_quantity", "decrease", product.name, 11)

        assert (
            f'Количество отнимаемого товара "{product.name}" не может быть больше его наличия'
            in str(exc_info.value)
        )
        stock.refresh_from_db()
        assert stock.quantity == 10


# ----------------- ТЕСТЫ ЭКСПОРТА И ИМПОРТА ОСТАТКОВ -----------------


def test_export_product_residue_command(tmp_path: Path, product: Product, stock: Stock):
    """Команда export_product_residue корректно выгружает остатки товаров в JSON-файл."""
    # Создаём путь к временному файлу внутри тестовой папки tmp_path
    output_file = tmp_path / "test_residue.json"

    out = StringIO()

    # Запускаем экспорт, передавая путь через флаг --file
    call_command("export_product_residue", file=str(output_file), stdout=out)

    # 1. Проверяем, что файл реально создался на диске
    assert output_file.exists()

    # 2. Читаем созданный JSON и проверяем его структуру и данные
    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    expected_data = [{"name": product.name, "quantity": stock.quantity}]
    assert data == expected_data

    # 3. Проверяем вывод сообщения об успехе в консоль
    assert f"Остатки успешно выгружены в {output_file}" in out.getvalue()


def test_load_goods_command_success(tmp_path: Path, product: Product, stock: Stock):
    """Команда load_goods корректно обновляет остатки товаров из JSON-файла."""
    assert stock.quantity == 10

    # Создаём временный JSON-файл с новыми остатками (например, 25 шт.)
    input_file = tmp_path / "import_residue.json"
    import_data = [{"name": product.name, "quantity": 25}]
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(import_data, f, ensure_ascii=False)

    out = StringIO()

    # Запускаем импорт
    call_command("load_goods", file=str(input_file), stdout=out)

    # 1. Проверяем, что количество в базе данных реально обновилось до 25
    stock.refresh_from_db()
    assert stock.quantity == 25

    # 2. Проверяем текст отчёта в консоли
    output = out.getvalue()
    assert (
        f'Количество товара "{product.name}" успешно обновлено и теперь составляет 25 шт.'
        in output
    )


@pytest.mark.django_db
def test_load_goods_command_product_not_found(tmp_path: Path):
    """Если товара из JSON нет в БД, load_goods пишет ошибку в stderr и не падает."""
    input_file = tmp_path / "unknown_goods.json"
    import_data = [{"name": "Несуществующий_Товар", "quantity": 50}]
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(import_data, f, ensure_ascii=False)

    err = StringIO()
    out = StringIO()

    # Вызываем команду с перехватом stderr
    call_command("load_goods", file=str(input_file), stdout=out, stderr=err)

    # Проверяем, что сообщение об ошибке попало именно в поток stderr
    assert "Товар 'Несуществующий_Товар' не найден в базе данных!" in err.getvalue()
    # И в базе такой товар не появился
    assert not Product.objects.filter(name="Несуществующий_Товар").exists()
