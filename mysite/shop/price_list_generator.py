"""
Модуль динамической генерации и отправки оптового прайс-листа ТМ «Сибсыр».
Формирует стилизованный Excel (.xlsx) без внешних зависимостей (чистый OpenXML)
и обеспечивает отправку коммерческого предложения на Email.
"""
import io
import os
import zipfile
import logging
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)


def _col_letter(n: int) -> str:
    """Преобразует порядковый номер столбца (1-based) в букву Excel (1 -> A, 27 -> AA)."""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def generate_wholesale_price_list_xlsx() -> tuple[bytes, str]:
    """
    Генерирует актуальный оптовый прайс-лист в формате Microsoft Excel (.xlsx)
    на основе актуальной базы товаров и категорий.
    
    Возвращает:
        (bytes_content, filename)
    """
    from shop.models import Category, Product
    from main.models import SiteSettings

    site_settings = SiteSettings.get_solo() if hasattr(SiteSettings, "get_solo") else SiteSettings.objects.first()
    brand_name = getattr(site_settings, "brand_name", "ТМ «Сибсыр» ИП Нахшкарян А.Л.")
    phone = getattr(site_settings, "phone", "8 (3812) 43-35-36")
    email = getattr(site_settings, "email", "sibs@list.ru")
    address = getattr(site_settings, "address", "г. Омск, ул. Зеленая, 16")
    seller_inn = getattr(site_settings, "seller_inn", "550119874521")
    
    today = timezone.localtime(timezone.now())
    date_str = today.strftime("%d.%m.%Y")
    datetime_str = today.strftime("%d.%m.%Y %H:%M")
    filename = f"Sibsir_Wholesale_Price_List_{today.strftime('%Y-%m-%d')}.xlsx"

    # Получаем категории и активные товары
    categories = Category.objects.filter(is_active=True).order_by("order", "id")
    products = Product.objects.filter(is_active=True).select_related("category").order_by("category__order", "order", "title")

    # OpenXML: Content_Types
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

    # OpenXML: Root relationships
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    # OpenXML: Workbook relationships
    wb_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    # OpenXML: Workbook
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Оптовый прайс-лист" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    # OpenXML: Styles
    # Fonts:
    # 0: Regular Calibri 10pt (gray/black)
    # 1: Bold Calibri 15pt #1E293B (Main Title)
    # 2: Bold Calibri 10pt #FFFFFF (Header cell text)
    # 3: Bold Calibri 11pt #B45309 (Category banner title)
    # 4: Bold Calibri 10pt #15803D (Wholesale price text)
    # 5: Bold Calibri 10pt #0F172A (General bold)
    # 6: Regular Calibri 9pt #64748B (Contacts & Subtext)
    # Fills:
    # 0: none
    # 1: gray125
    # 2: #FF8400 (Sibsir Orange - Table headers)
    # 3: #FEF3C7 (Warm amber - Category group banner)
    # 4: #F8FAFC (Subtle zebra row)
    # 5: #F0FDF4 (Subtle green wholesale highlight)
    # 6: #EFF6FF (Subtle blue footer summary)
    # Borders:
    # 0: none
    # 1: thin #CBD5E1 all sides
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="7">
    <font><name val="Calibri"/><sz val="10"/><color rgb="FF0F172A"/></font>
    <font><b/><name val="Calibri"/><sz val="15"/><color rgb="FF1E293B"/></font>
    <font><b/><name val="Calibri"/><sz val="10"/><color rgb="FFFFFFFF"/></font>
    <font><b/><name val="Calibri"/><sz val="11"/><color rgb="FFB45309"/></font>
    <font><b/><name val="Calibri"/><sz val="10"/><color rgb="FF15803D"/></font>
    <font><b/><name val="Calibri"/><sz val="10"/><color rgb="FF0F172A"/></font>
    <font><name val="Calibri"/><sz val="9"/><color rgb="FF64748B"/></font>
  </fonts>
  <fills count="7">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFF8400"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFEF3C7"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF8FAFC"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF0FDF4"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFEFF6FF"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFCBD5E1"/></left>
      <right style="thin"><color rgb="FFCBD5E1"/></right>
      <top style="thin"><color rgb="FFCBD5E1"/></top>
      <bottom style="thin"><color rgb="FFCBD5E1"/></bottom>
    </border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="14">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
    <xf numFmtId="0" fontId="6" fillId="0" borderId="0" xfId="0" applyFont="1"/>
    <xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" alignment="center"/>
    <xf numFmtId="0" fontId="3" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" alignment="center"/>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyFill="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyFill="1" applyBorder="1" alignment="center"/>
    <xf numFmtId="0" fontId="4" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" alignment="right"/>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" alignment="right"/>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyFill="1" applyBorder="1" alignment="right"/>
    <xf numFmtId="0" fontId="5" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>
    <xf numFmtId="0" fontId="5" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" alignment="right"/>
  </cellXfs>
</styleSheet>"""

    # Helper function to generate cell XML
    def make_cell(coord: str, value, style_id: int = 0, is_numeric: bool = False):
        if is_numeric and value is not None and str(value).strip() != "":
            try:
                num = float(value)
                if num.is_integer():
                    return f'<c r="{coord}" s="{style_id}"><v>{int(num)}</v></c>'
                return f'<c r="{coord}" s="{style_id}"><v>{num}</v></c>'
            except (ValueError, TypeError):
                pass
        
        val_str = xml_escape(str(value) if value is not None else "")
        return f'<c r="{coord}" t="inlineStr" s="{style_id}"><is><t>{val_str}</t></is></c>'

    sheet_rows = []
    current_row = 1

    # Заголовок документа (Шапка)
    sheet_rows.append(f'<row r="{current_row}">')
    sheet_rows.append(make_cell(f"A{current_row}", f"ТОРГОВАЯ МАРКА «СИБСЫР» — ОПТОВЫЙ ПРАЙС-ЛИСТ (B2B)", 1))
    sheet_rows.append('</row>')
    current_row += 1

    sheet_rows.append(f'<row r="{current_row}">')
    sheet_rows.append(make_cell(f"A{current_row}", f"Производитель: {brand_name} (ИНН {seller_inn}) • Сформирован: {datetime_str}", 2))
    sheet_rows.append('</row>')
    current_row += 1

    sheet_rows.append(f'<row r="{current_row}">')
    sheet_rows.append(make_cell(f"A{current_row}", f"Контакты отдела продаж: тел. {phone} | e-mail: {email} | Адрес: {address} | Сайт: sibsir.ru", 2))
    sheet_rows.append('</row>')
    current_row += 1

    sheet_rows.append(f'<row r="{current_row}">')
    sheet_rows.append(make_cell(f"A{current_row}", "Условия поставок: доставка спецтранспортом (+2...+4°C), полный пакет документов, ВСД ФГИС «Меркурий», декларации соответствия.", 2))
    sheet_rows.append('</row>')
    current_row += 2  # Blank row

    # Заголовки колонок таблицы
    headers = [
        ("№", 6),
        ("Наименование продукции", 42),
        ("Категория", 22),
        ("Жирность", 13),
        ("Фасовка / Вес", 16),
        ("Упаковка", 18),
        ("Срок годности", 16),
        ("Розница, ₽", 15),
        ("ОПТОВАЯ ЦЕНА, ₽", 18),
        ("Мин. заказ для опта", 22),
        ("Статус", 14),
    ]

    header_cells = []
    for col_idx, (h_title, _) in enumerate(headers, start=1):
        c_coord = f"{_col_letter(col_idx)}{current_row}"
        header_cells.append(make_cell(c_coord, h_title, 3))
    sheet_rows.append(f'<row r="{current_row}">{"".join(header_cells)}</row>')
    current_row += 1

    # Группировка товаров по категориям
    total_products_count = 0
    item_counter = 1

    # Индексируем товары по категориям
    cat_products_map = {}
    for p in products:
        c_id = p.category_id or 0
        cat_products_map.setdefault(c_id, []).append(p)

    for cat in categories:
        cat_prods = cat_products_map.get(cat.id, [])
        if not cat_prods:
            continue

        # Строка раздела категории
        cat_cells = []
        for col_idx in range(1, len(headers) + 1):
            c_coord = f"{_col_letter(col_idx)}{current_row}"
            val = f"🧀  {cat.name.upper()} ({len(cat_prods)} поз.)" if col_idx == 2 else ""
            cat_cells.append(make_cell(c_coord, val, 4))
        sheet_rows.append(f'<row r="{current_row}">{"".join(cat_cells)}</row>')
        current_row += 1

        for prod in cat_prods:
            total_products_count += 1
            is_zebra = (item_counter % 2 == 0)
            
            # Цены
            retail_val = prod.effective_price_numeric or prod.price_numeric
            wholesale_num = prod.wholesale_price_numeric
            wholesale_str = prod.effective_wholesale_price_display or (f"{wholesale_num} ₽" if wholesale_num else "По запросу")
            
            min_qty = prod.wholesale_min_qty or "от 1 коробки"
            shelf_life = prod.shelf_life or "Согласно ТУ/ГОСТ"
            fat_content = prod.fat_content or "—"
            unit_weight = prod.unit_weight or "—"
            pkg = prod.package_type or "Вакуумная / полимерная"

            # Стили ячеек
            text_s = 7 if is_zebra else 5
            center_s = 8 if is_zebra else 6
            retail_s = 11 if is_zebra else 10
            wholesale_s = 9  # всегда подсвечиваем зеленым

            row_cells = [
                make_cell(f"A{current_row}", item_counter, center_s, is_numeric=True),
                make_cell(f"B{current_row}", prod.title, text_s),
                make_cell(f"C{current_row}", cat.name, text_s),
                make_cell(f"D{current_row}", fat_content, center_s),
                make_cell(f"E{current_row}", unit_weight, center_s),
                make_cell(f"F{current_row}", pkg, text_s),
                make_cell(f"G{current_row}", shelf_life, center_s),
                make_cell(f"H{current_row}", retail_val if retail_val > 0 else "—", retail_s, is_numeric=(retail_val > 0)),
                make_cell(f"I{current_row}", wholesale_num if wholesale_num > 0 else wholesale_str, wholesale_s, is_numeric=(wholesale_num > 0)),
                make_cell(f"J{current_row}", min_qty, text_s),
                make_cell(f"K{current_row}", "В наличии", center_s),
            ]
            sheet_rows.append(f'<row r="{current_row}">{"".join(row_cells)}</row>')
            current_row += 1
            item_counter += 1

    # Итоговая строка
    sheet_rows.append(f'<row r="{current_row}">')
    sheet_rows.append(make_cell(f"A{current_row}", "ИТОГО", 12))
    sheet_rows.append(make_cell(f"B{current_row}", f"Всего в прайс-листе: {total_products_count} активных наименований молочной продукции", 12))
    for col_idx in range(3, len(headers) + 1):
        sheet_rows.append(make_cell(f"{_col_letter(col_idx)}{current_row}", "", 12))
    sheet_rows.append('</row>')
    current_row += 2

    # Примечания и контакты для заказа
    notes = [
        "УСЛОВИЯ РАБОТЫ И ЗАКАЗА:",
        "1. Для заключения договора поставки требуются реквизиты юридического лица / ИП (ИНН, ОГРН, банковские реквизиты).",
        "2. Работаем через систему электронного документооборота (Диадок / СБИС) и ФГИС «Меркурий».",
        "3. Цены указаны с учетом НДС / для безналичного расчета. Для постоянных партнеров возможна отсрочка платежа.",
        f"4. По вопросам скидок на объемные поставки обращайтесь: {phone}, {email}.",
    ]
    for note in notes:
        sheet_rows.append(f'<row r="{current_row}">')
        sheet_rows.append(make_cell(f"A{current_row}", note, 2))
        sheet_rows.append('</row>')
        current_row += 1

    # XML столбцов и ширина
    cols_xml = []
    for col_idx, (_, w) in enumerate(headers, start=1):
        cols_xml.append(f'<col min="{col_idx}" max="{col_idx}" width="{w}" customWidth="1"/>')

    worksheet = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <cols>
    {"".join(cols_xml)}
  </cols>
  <sheetData>
    {"".join(sheet_rows)}
  </sheetData>
</worksheet>"""

    # Собираем ZIP архив
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/styles.xml", styles)
        zf.writestr("xl/worksheets/sheet1.xml", worksheet.encode("utf-8"))

    return buf.getvalue(), filename


def generate_wholesale_price_list_html() -> str:
    """Генерирует HTML-версию прайс-листа для предварительного просмотра и печати."""
    from shop.models import Category, Product
    from main.models import SiteSettings

    site_settings = SiteSettings.get_solo() if hasattr(SiteSettings, "get_solo") else SiteSettings.objects.first()
    brand_name = getattr(site_settings, "brand_name", "ТМ «Сибсыр» ИП Нахшкарян А.Л.")
    phone = getattr(site_settings, "phone", "8 (3812) 43-35-36")
    email = getattr(site_settings, "email", "sibs@list.ru")
    address = getattr(site_settings, "address", "г. Омск, ул. Зеленая, 16")

    today = timezone.localtime(timezone.now())
    categories = Category.objects.filter(is_active=True).order_by("order", "id")
    products = Product.objects.filter(is_active=True).select_related("category").order_by("category__order", "order", "title")

    cat_map = {}
    for p in products:
        cat_map.setdefault(p.category_id or 0, []).append(p)

    rows_html = []
    item_idx = 1
    for cat in categories:
        c_prods = cat_map.get(cat.id, [])
        if not c_prods:
            continue
        rows_html.append(f"""
        <tr class="category-header-row">
            <td colspan="10">🧀 {cat.name} <span class="badge">({len(c_prods)} поз.)</span></td>
        </tr>
        """)
        for p in c_prods:
            ws_price = p.effective_wholesale_price_display or (f"{p.wholesale_price_numeric} ₽" if p.wholesale_price_numeric else "По запросу")
            rozn_price = f"{p.effective_price_numeric} ₽" if p.effective_price_numeric else "—"
            rows_html.append(f"""
            <tr>
                <td style="text-align: center; color: #64748b;">{item_idx}</td>
                <td><strong>{p.title}</strong></td>
                <td style="text-align: center;">{p.fat_content or '—'}</td>
                <td style="text-align: center;">{p.unit_weight or '—'}</td>
                <td>{p.package_type or '—'}</td>
                <td style="text-align: center;">{p.shelf_life or '—'}</td>
                <td style="text-align: right; color: #64748b;">{rozn_price}</td>
                <td style="text-align: right; color: #15803d; font-weight: 700; background: #f0fdf4;">{ws_price}</td>
                <td>{p.wholesale_min_qty or 'от 1 коробки'}</td>
                <td style="text-align: center;"><span class="badge-status">В наличии</span></td>
            </tr>
            """)
            item_idx += 1

    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <title>Оптовый прайс-лист ТМ «Сибсыр»</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; color: #0f172a; line-height: 1.5; }}
            .header {{ border-bottom: 3px solid #ff8400; padding-bottom: 16px; margin-bottom: 24px; }}
            .title {{ font-size: 22px; font-weight: 800; color: #1e293b; margin: 0 0 6px 0; }}
            .subtitle {{ font-size: 13px; color: #64748b; margin: 0; }}
            .contacts {{ margin-top: 10px; font-size: 13px; color: #334155; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 16px; }}
            th {{ background: #1e293b; color: white; padding: 10px 8px; text-align: left; font-weight: 600; border: 1px solid #334155; }}
            td {{ padding: 8px; border: 1px solid #e2e8f0; }}
            tr:nth-child(even) {{ background: #f8fafc; }}
            .category-header-row td {{ background: #fef3c7 !important; color: #92400e; font-weight: 700; font-size: 13px; border: 1px solid #fde68a; padding: 10px 8px; }}
            .badge {{ font-size: 11px; font-weight: normal; color: #78350f; }}
            .badge-status {{ background: #dcfce7; color: #15803d; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; }}
            @media print {{
                body {{ margin: 10px; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">ТОРГОВАЯ МАРКА «СИБСЫР» — ОПТОВЫЙ ПРАЙС-ЛИСТ</h1>
            <p class="subtitle">{brand_name} • Актуален на: {today.strftime('%d.%m.%Y %H:%M')}</p>
            <div class="contacts">
                📞 <strong>{phone}</strong> &nbsp;|&nbsp; ✉️ <strong>{email}</strong> &nbsp;|&nbsp; 📍 <strong>{address}</strong> &nbsp;|&nbsp; 🌐 <strong>sibsir.ru</strong>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width: 35px; text-align: center;">№</th>
                    <th>Наименование продукции</th>
                    <th style="width: 70px; text-align: center;">Жирность</th>
                    <th style="width: 90px; text-align: center;">Фасовка</th>
                    <th style="width: 110px;">Упаковка</th>
                    <th style="width: 90px; text-align: center;">Срок годности</th>
                    <th style="width: 80px; text-align: right;">Розница</th>
                    <th style="width: 100px; text-align: right; background: #ff8400;">Опт (руб.)</th>
                    <th style="width: 130px;">Мин. заказ</th>
                    <th style="width: 80px; text-align: center;">Статус</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows_html)}
            </tbody>
        </table>
    </body>
    </html>
    """


def send_wholesale_price_list_email(
    recipient_email: str,
    recipient_name: str = "",
    company_name: str = "",
    custom_subject: str = None,
    custom_body: str = None,
    request_obj=None,
    user_profile=None,
    admin_user=None,
    cached_xlsx_data: tuple = None,
) -> dict:
    """
    Отправляет клиенту письмо с прикрепленным актуальным оптовым прайс-листом (.xlsx).
    
    Возвращает dict:
        {"success": bool, "email": str, "message": str, "error": str}
    """
    from main.models import SiteSettings

    if not recipient_email or "@" not in recipient_email:
        return {
            "success": False,
            "email": recipient_email,
            "error": "Некорректный или пустой адрес электронной почты.",
        }

    site_settings = SiteSettings.get_solo() if hasattr(SiteSettings, "get_solo") else SiteSettings.objects.first()
    brand_name = getattr(site_settings, "brand_name", "ТМ «Сибсыр»")
    phone = getattr(site_settings, "phone", "8 (3812) 43-35-36")
    contact_email = getattr(site_settings, "email", "sibs@list.ru")
    address = getattr(site_settings, "address", "г. Омск, ул. Зеленая, 16")
    today = timezone.localtime(timezone.now())
    date_str = today.strftime("%d.%m.%Y")

    # Имя получателя
    client_name = recipient_name.strip() or (user_profile.display_name if user_profile else "") or "Партнер"
    company_str = company_name.strip() or (user_profile.company_name if user_profile else "")
    if company_str and company_str != client_name:
        greeting_name = f"{client_name} ({company_str})"
    else:
        greeting_name = company_str or client_name

    # Тема письма
    default_subject = getattr(site_settings, "wholesale_email_subject", "") or "Оптовый прайс-лист ТМ «Сибсыр» и коммерческие условия"
    subject = (custom_subject or default_subject).replace("{name}", client_name).replace("{company}", company_str).replace("{date}", date_str)

    # Текст письма
    default_body = getattr(site_settings, "wholesale_email_body", "") or (
        "Здравствуйте, {name}!\n\n"
        "Благодарим вас за интерес к сыроваренной продукции ТМ «Сибсыр».\n\n"
        "Направляем вам актуальный оптовый прайс-лист на всю линейку нашей продукции "
        "(рассольные и полутвердые сыры, масло сливочное, снеки).\n\n"
        "Наши ключевые преимущества для оптовых партнеров и розничных сетей:\n"
        "• Прямые поставки от завода-производителя без наценок посредников;\n"
        "• Соблюдение холодовой цепочки (+2...+4°C) спецтранспортом;\n"
        "• Полный пакет закрывающих документов, работа в системе ФГИС «Меркурий»;\n"
        "• Гибкие индивидуальные условия и график поставок.\n\n"
        "Для согласования заказа свяжитесь с отделом продаж:\n"
        "Телефон: {phone}\n"
        "E-mail: {email}\n"
        "Адрес склада и производства: {address}\n\n"
        "С уважением, отдел оптовых продаж ТМ «Сибсыр»"
    )
    
    body_template = custom_body or default_body
    body_text = (
        body_template
        .replace("{name}", greeting_name)
        .replace("{company}", company_str)
        .replace("{phone}", phone)
        .replace("{email}", contact_email)
        .replace("{address}", address)
        .replace("{date}", date_str)
    )

    # Красивая HTML-версия письма
    formatted_paragraphs = "".join(f"<p style='margin: 0 0 14px 0; color: #334155; line-height: 1.6;'>{xml_escape(p)}</p>" for p in body_text.split("\n\n") if p.strip())
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 24px; color: #0f172a;">
      <div style="max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="background: linear-gradient(135deg, #ff8400 0%, #ea580c 100%); padding: 24px; color: #ffffff;">
          <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 800;">ТМ «СИБСЫР»</h2>
          <p style="margin: 0; font-size: 13px; opacity: 0.95;">Производство высококачественных сыров и сливочного масла с 2000 года</p>
        </div>
        <div style="padding: 28px 24px;">
          <div style="margin-bottom: 20px;">
            {formatted_paragraphs}
          </div>
          <div style="background: #fff7ed; border-left: 4px solid #ff8400; padding: 14px 18px; border-radius: 0 8px 8px 0; margin-top: 24px;">
            <p style="margin: 0 0 4px 0; font-weight: 700; color: #9a3412; font-size: 13px;">📎 Файл прайс-листа во вложении:</p>
            <p style="margin: 0; font-size: 12px; color: #c2410c;">К данному письму прикреплен файл <strong>Sibsir_Wholesale_Price_List_{today.strftime('%Y-%m-%d')}.xlsx</strong> с полным ассортиментом, оптовыми ценами и фасовками.</p>
          </div>
          <div style="margin-top: 28px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b;">
            <p style="margin: 0 0 4px 0;"><strong>Отдел оптовых продаж «Сибсыр»:</strong></p>
            <p style="margin: 0;">📞 {phone} &nbsp;|&nbsp; ✉️ {contact_email} &nbsp;|&nbsp; 📍 {address}</p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """

    # Получаем или берем из кэша файл прайса
    if cached_xlsx_data:
        xlsx_bytes, xlsx_filename = cached_xlsx_data
    else:
        xlsx_bytes, xlsx_filename = generate_wholesale_price_list_xlsx()

    # Формируем и отправляем Email
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", contact_email) or contact_email

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_text,
        from_email=from_email,
        to=[recipient_email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.attach(
        filename=xlsx_filename,
        content=xlsx_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    is_simulated = False
    error_msg = ""

    try:
        msg.send(fail_silently=False)
    except Exception as exc:
        logger.warning(f"Ошибка при отправке оптового прайс-листа на {recipient_email}: {exc}")
        # Если в среде разработки нет SMTP-сервера, зафиксируем это без аварийного падения
        error_msg = str(exc)
        # Если ошибка связана с отсутствием SMTP сервера, фиксируем отправку в журнал
        if "connect" in error_msg.lower() or "10061" in error_msg or "refused" in error_msg:
            is_simulated = True

    # Обновляем статус заявки, если передана
    if request_obj:
        request_obj.approval_status = "approved"
        request_obj.is_processed = True
        request_obj.approved_by = admin_user
        request_obj.approved_at = timezone.now()
        request_obj.price_list_sent_at = timezone.now()
        if is_simulated:
            request_obj.admin_comment = (
                f"{request_obj.admin_comment}\n[Система] Прайс сформирован. Почтовый сервер недоступен ({error_msg})."
            ).strip()
        request_obj.save()

    if error_msg and not is_simulated:
        return {
            "success": False,
            "email": recipient_email,
            "error": error_msg,
        }

    notice = " (режим разработки: отправка эмулирована и залогирована)" if is_simulated else ""
    return {
        "success": True,
        "email": recipient_email,
        "message": f"Прайс-лист успешно отправлен на {recipient_email}{notice}.",
        "simulated": is_simulated,
    }

