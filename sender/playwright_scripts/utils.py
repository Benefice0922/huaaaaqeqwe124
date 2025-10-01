import re
import html

# --- Словарь соответствия тегов и их описаний ---
PLACEHOLDER_LABELS = {
    "[Name]": "Имя пользователя",
    "[Price]": "Цена",
    "[Title]": "Название объявления",
    # Можно добавить другие теги
    # "[Link]": "Ссылка на объявление",
    # "[Date]": "Дата публикации",
}

def replace_placeholders(text: str, **kwargs) -> str:
    """
    Умная замена тегов в тексте на значения из kwargs.
    Поддерживает [Name], {Name}, [name], {name} и любые другие ключи.
    Автоматически экранирует HTML для безопасности.

    Пример:
        text = "ку [Name], [Price], [Title]"
        kwargs = {"name": "Алия", "price": "1000 KGS", "title": "BMW"}
        -> "ку Алия, 1000 KGS, BMW"
    """
    if not text:
        return ""

    result = text

    # Для каждого ключа подставим все варианты: [key], {key}, [Key], {Key}
    for key, value in kwargs.items():
        if value is not None:
            safe_value = html.escape(str(value))
            # Заменить все варианты скобок и регистра
            for tmpl in [f"[{key}]", f"{{{key}}}", f"[{key.capitalize()}]", f"{{{key.capitalize()}}}"]:
                result = result.replace(tmpl, safe_value)
    return result

def extract_price(price_text: str) -> str | None:
    """
    Извлекает числовое значение цены из строки.
    Например: "1 500 000 тг." -> "1500000"

    Args:
        price_text (str): Строка с ценой.
    Returns:
        str | None: Очищенное числовое значение цены или None.
    """
    if not price_text:
        return None
    cleaned = re.sub(r'[^\d]', '', price_text)
    return cleaned if cleaned else None