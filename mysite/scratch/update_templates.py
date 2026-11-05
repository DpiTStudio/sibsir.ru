import os

# 1. Update footer.html
footer_path = 'mysite/templates/includes/footer.html'
with open(footer_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '&copy; 1999–2026 ТМ «Сибсыр» (arevtur.rf). Все права защищены.',
    '&copy; 1999–2026 ТМ «Сибсыр» (sibsir.ru). Все права защищены.'
)

# Add legal links into footer-bottom-row
old_footer_bottom = '&copy; 1999–2026 ТМ «Сибсыр» (sibsir.ru). Все права защищены.\r\n                </div>'
if old_footer_bottom not in text:
    old_footer_bottom = '&copy; 1999–2026 ТМ «Сибсыр» (sibsir.ru). Все права защищены.\n                </div>'

new_footer_bottom = '''&copy; 1999–2026 ТМ «Сибсыр» (sibsir.ru). Все права защищены.
                </div>
                <div class="d-flex flex-wrap gap-2 gap-md-3 small text-secondary">
                    <a href="{% url 'main:company_consent' %}" class="footer-legal-link text-secondary text-decoration-none">Политика конфиденциальности</a>
                    <span class="text-muted">•</span>
                    <a href="{% url 'main:company_soglasie' %}" class="footer-legal-link text-secondary text-decoration-none">Согласие на обработку данных</a>
                </div>'''

text = text.replace(old_footer_bottom, new_footer_bottom, 1)

old_mgmt_crlf = '<div>\r\n                    Сайт работает под управлением\r\n                </div>'
old_mgmt_lf = '<div>\n                    Сайт работает под управлением\n                </div>'
new_mgmt = '''<div class="small text-secondary">
                    Официальный сайт: <a href="https://sibsir.ru/" class="text-white text-decoration-none fw-semibold">sibsir.ru</a>
                </div>'''

if old_mgmt_crlf in text:
    text = text.replace(old_mgmt_crlf, new_mgmt)
elif old_mgmt_lf in text:
    text = text.replace(old_mgmt_lf, new_mgmt)

with open(footer_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('footer.html updated')

# 2. Update modal_callback.html
cb_path = 'mysite/templates/includes/modals/modal_callback.html'
with open(cb_path, 'r', encoding='utf-8') as f:
    cb_text = f.read()

cb_btn = '</button>\r\n                    </form>'
if cb_btn not in cb_text:
    cb_btn = '</button>\n                    </form>'

cb_replacement = '''</button>
                        <div class="text-center text-muted small mt-2" style="font-size: 0.75rem;">
                            Нажимая кнопку, вы соглашаетесь с <a href="{% url 'main:company_consent' %}" target="_blank" class="text-decoration-underline text-muted">Политикой конфиденциальности</a> и даете <a href="{% url 'main:company_soglasie' %}" target="_blank" class="text-decoration-underline text-muted">согласие на обработку данных</a>
                        </div>
                    </form>'''

if 'company_consent' not in cb_text:
    cb_text = cb_text.replace(cb_btn, cb_replacement, 1)
    with open(cb_path, 'w', encoding='utf-8') as f:
        f.write(cb_text)
    print('modal_callback.html updated')

# 3. Update modal_quick_buy.html
qb_path = 'mysite/templates/includes/modals/modal_quick_buy.html'
with open(qb_path, 'r', encoding='utf-8') as f:
    qb_text = f.read()

qb_btn = '</button>\r\n                    </form>'
if qb_btn not in qb_text:
    qb_btn = '</button>\n                    </form>'

qb_replacement = '''</button>
                        <div class="text-center text-muted small mt-2" style="font-size: 0.75rem;">
                            Нажимая кнопку, вы соглашаетесь с <a href="{% url 'main:company_consent' %}" target="_blank" class="text-decoration-underline text-muted">Политикой конфиденциальности</a> и даете <a href="{% url 'main:company_soglasie' %}" target="_blank" class="text-decoration-underline text-muted">согласие на обработку данных</a>
                        </div>
                    </form>'''

if 'company_consent' not in qb_text:
    qb_text = qb_text.replace(qb_btn, qb_replacement, 1)
    with open(qb_path, 'w', encoding='utf-8') as f:
        f.write(qb_text)
    print('modal_quick_buy.html updated')

# 4. Update contacts_feedback.html
cf_path = 'mysite/templates/main/index_sections/contacts_feedback.html'
with open(cf_path, 'r', encoding='utf-8') as f:
    cf_text = f.read()

cf_btn = '</button>\r\n                    </form>'
if cf_btn not in cf_text:
    cf_btn = '</button>\n                    </form>'

cf_replacement = '''</button>
                        <div class="text-center text-muted small mt-2" style="font-size: 0.75rem;">
                            Нажимая кнопку, вы соглашаетесь с <a href="{% url 'main:company_consent' %}" target="_blank" class="text-decoration-underline text-muted">Политикой конфиденциальности</a> и даете <a href="{% url 'main:company_soglasie' %}" target="_blank" class="text-decoration-underline text-muted">согласие на обработку данных</a>
                        </div>
                    </form>'''

if 'company_consent' not in cf_text:
    cf_text = cf_text.replace(cf_btn, cf_replacement, 1)
    with open(cf_path, 'w', encoding='utf-8') as f:
        f.write(cf_text)
    print('contacts_feedback.html updated')

# 5. Update contacts.html
ct_path = 'mysite/templates/main/contacts.html'
with open(ct_path, 'r', encoding='utf-8') as f:
    ct_text = f.read()

ct_old = '<div class="text-center text-muted small mt-2" style="font-size: 0.75rem;">\r\n                        Нажимая кнопку, вы соглашаетесь на обработку персональных данных\r\n                    </div>'
if ct_old not in ct_text:
    ct_old = '<div class="text-center text-muted small mt-2" style="font-size: 0.75rem;">\n                        Нажимая кнопку, вы соглашаетесь на обработку персональных данных\n                    </div>'

ct_new = '''<div class="text-center text-muted small mt-2" style="font-size: 0.75rem;">
                        Нажимая кнопку, вы соглашаетесь с <a href="{% url 'main:company_consent' %}" target="_blank" class="text-decoration-underline text-muted">Политикой конфиденциальности</a> и даете <a href="{% url 'main:company_soglasie' %}" target="_blank" class="text-decoration-underline text-muted">согласие на обработку данных</a>
                    </div>'''

if ct_old in ct_text:
    ct_text = ct_text.replace(ct_old, ct_new, 1)
    with open(ct_path, 'w', encoding='utf-8') as f:
        f.write(ct_text)
    print('contacts.html updated')

print('All template updates finished.')

