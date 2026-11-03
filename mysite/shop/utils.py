"""
Утилиты для формирования документов: сумма прописью на русском языке и форматирование чисел.
"""
from decimal import Decimal

# Склонения числительных
UNITS_MALE = [
    "", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"
]
UNITS_FEMALE = [
    "", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"
]
TEENS = [
    "десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать",
    "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"
]
TENS = [
    "", "", "двадцать", "тридцать", "сорок", "пятьдесят",
    "шестьдесят", "семьдесят", "восемьдесят", "девяносто"
]
HUNDREDS = [
    "", "сто", "двести", "триста", "четыреста", "пятьсот",
    "шестьсот", "семьсот", "восемьсот", "девятьсот"
]

ORDERS = [
    # (male/female, 1, 2-4, 5-0)
    ("female", "тысяча", "тысячи", "тысяч"),
    ("male", "миллион", "миллиона", "миллионов"),
    ("male", "миллиард", "миллиарда", "миллиардов"),
]


def plural_form(n: int, forms: tuple) -> str:
    """Выбор правильной грамматической формы слова по числу."""
    n = abs(n) % 100
    n1 = n % 10
    if 10 < n < 20:
        return forms[2]
    if 1 < n1 < 5:
        return forms[1]
    if n1 == 1:
        return forms[0]
    return forms[2]


def triad_to_words(number: int, is_female: bool = False) -> str:
    """Преобразует трехзначное число в слова."""
    h = number // 100
    t = (number % 100) // 10
    u = number % 10
    words = []

    if h > 0:
        words.append(HUNDREDS[h])

    if t == 1:
        words.append(TEENS[u])
    else:
        if t > 1:
            words.append(TENS[t])
        if u > 0:
            units = UNITS_FEMALE if is_female else UNITS_MALE
            words.append(units[u])

    return " ".join(words)


def number_to_words(num: int, is_female: bool = False) -> str:
    """Целое число прописью на русском языке."""
    if num == 0:
        return "ноль"

    triads = []
    temp = num
    while temp > 0:
        triads.append(temp % 1000)
        temp //= 1000

    parts = []
    # Первые 3 разряда (единицы)
    if len(triads) > 0 and triads[0] > 0:
        parts.insert(0, triad_to_words(triads[0], is_female=is_female))

    # Тысячи, миллионы, миллиарды
    for idx, triad in enumerate(triads[1:]):
        if triad > 0:
            gender, f1, f2, f5 = ORDERS[idx]
            tw = triad_to_words(triad, is_female=(gender == "female"))
            form = plural_form(triad, (f1, f2, f5))
            parts.insert(0, f"{tw} {form}")

    return " ".join(parts).strip()


def amount_in_words(amount) -> str:
    """
    Преобразует сумму в рублях в строку прописью с копейками.
    Пример: 1540.50 -> 'Одна тысяча пятьсот сорок рублей 50 копеек'
    """
    try:
        val = Decimal(str(amount))
    except Exception:
        val = Decimal("0.00")

    rubles = int(val)
    kopecks = int(round((val - rubles) * 100))

    rubles_words = number_to_words(rubles, is_female=False)
    rubles_form = plural_form(rubles, ("рубль", "рубля", "рублей"))
    kopecks_form = plural_form(kopecks, ("копейка", "копейки", "копеек"))

    if not rubles_words:
        rubles_words = "ноль"

    capitalized = rubles_words[0].upper() + rubles_words[1:] if rubles_words else "Ноль"
    return f"{capitalized} {rubles_form} {kopecks:02d} {kopecks_form}"


def count_items_in_words(count: int) -> str:
    """Количество наименований прописью: '3' -> 'три'."""
    res = number_to_words(count, is_female=False)
    return res
