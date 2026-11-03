import io
import random
import uuid
import base64
from PIL import Image, ImageDraw, ImageFont
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.cache import cache

CAPTCHA_SIGNER_SALT = "sib_security_captcha_salt_2026"
signer = TimestampSigner(salt=CAPTCHA_SIGNER_SALT)

# Символы для буквенно-цифровой капчи (без визуально неоднозначных 0, O, 1, I, l)
CHARSET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def get_captcha_font(size=25):
    """Пытается загрузить системный шрифт Arial или системный TrueType, иначе fallback."""
    for font_name in ["arial.ttf", "calibri.ttf", "segoeui.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_captcha(captcha_type="math"):
    """
    Генерирует новую капчу:
    - 'math': Простой арифметический пример (например: 14 + 7 = ?)
    - 'image': Набор из 4-5 символов с графическим шумом и защитными линиями
    Возвращает словарь:
    {
        'key': signed_token,
        'image_url': 'data:image/png;base64,...',
        'placeholder': '...',
        'type': captcha_type
    }
    """
    if captcha_type == "image":
        # Буквенно-цифровая капча
        code_length = random.choice([4, 5])
        code = "".join(random.choice(CHARSET) for _ in range(code_length))
        display_text = " ".join(list(code))
        answer = code.upper()
        placeholder = "Код с картинки"
    else:
        # Математическая капча
        op = random.choice(["+", "-"])
        if op == "+":
            a = random.randint(3, 35)
            b = random.randint(2, 25)
            ans = a + b
        else:
            a = random.randint(10, 45)
            b = random.randint(1, a - 1)
            ans = a - b
        display_text = f"{a} {op} {b} = ?"
        answer = str(ans)
        placeholder = "Ответ на пример"

    # Создание изображения
    width, height = 160, 46
    # Теплый светлый фон сыроварни
    bg_color = (252, 253, 255)
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Защитная рамка
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(226, 232, 240), width=1)

    # 2. Тонкие фоновые линии защиты
    line_colors = [
        (254, 215, 170), # мягкий оранжевый
        (226, 232, 240), # мягкий серый
        (191, 219, 254), # мягкий голубой
    ]
    for _ in range(4):
        x1 = random.randint(0, width // 3)
        y1 = random.randint(5, height - 5)
        x2 = random.randint(width // 2, width)
        y2 = random.randint(5, height - 5)
        color = random.choice(line_colors)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    # 3. Легкий точечный шум
    for _ in range(35):
        px = random.randint(2, width - 3)
        py = random.randint(2, height - 3)
        draw.point((px, py), fill=random.choice(line_colors))

    # 4. Отрисовка текста
    font = get_captcha_font(size=23)
    text_color = (30, 41, 59) # глубокий графитовый

    # Центрируем текст
    try:
        bbox = draw.textbbox((0, 0), display_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except Exception:
        text_w = len(display_text) * 11
        text_h = 20

    start_x = max(8, (width - text_w) // 2)
    start_y = max(6, (height - text_h) // 2 - 2)

    # Небольшая тень для объема
    draw.text((start_x + 1, start_y + 1), display_text, fill=(241, 245, 249), font=font)
    draw.text((start_x, start_y), display_text, fill=text_color, font=font)

    # 5. Сохранение в PNG и конвертация в Data URI
    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    b64_img = base64.b64encode(buffer.getvalue()).decode("ascii")
    image_url = f"data:image/png;base64,{b64_img}"

    # 6. Подпись ответа с помощью TimestampSigner
    salt_hash = uuid.uuid4().hex[:8]
    payload = f"{answer.lower()}:{salt_hash}"
    signed_token = signer.sign(payload)

    return {
        "key": signed_token,
        "image_url": image_url,
        "placeholder": placeholder,
        "type": captcha_type,
    }


def verify_captcha(token, user_answer, max_age=600):
    """
    Проверяет ответ пользователя.
    - token: зашифрованный токен из скрытого поля captcha_key
    - user_answer: ответ, введенный клиентом
    - max_age: срок жизни капчи в секундах (по умолчанию 10 минут)
    Возвращает (is_valid: bool, error_message: str)
    """
    if not token or not str(token).strip():
        return False, "Пожалуйста, введите проверочный код."

    if not user_answer or not str(user_answer).strip():
        return False, "Поле проверочного кода не может быть пустым."

    # Проверка цифровой подписи и времени
    try:
        payload = signer.unsign(token.strip(), max_age=max_age)
    except SignatureExpired:
        return False, "Время действия проверочного кода истекло. Пожалуйста, обновите код."
    except BadSignature:
        return False, "Неверный проверочный ключ. Пожалуйста, обновите код."

    # Защита от повторного использования одного и того же токена (Anti-replay)
    token_cache_key = f"sib_captcha_used_{token[-32:]}"
    if cache.get(token_cache_key):
        return False, "Этот проверочный код уже был использован. Пожалуйста, запросите новый код."

    try:
        expected_answer, _ = payload.split(":", 1)
    except ValueError:
        return False, "Ошибка формата проверочного токена."

    clean_user = "".join(str(user_answer).strip().lower().split())
    clean_expected = "".join(expected_answer.strip().lower().split())

    if clean_user != clean_expected:
        return False, "Неверный проверочный код или ответ на пример. Попробуйте снова."

    # Отмечаем токен как использованный
    cache.set(token_cache_key, "1", timeout=max_age)
    return True, ""
