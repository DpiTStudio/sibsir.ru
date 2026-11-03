# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, '/var/www/u3706063/data/www/sibsir.ru/mysite')
sys.path.insert(1, '/var/www/u3706063/data/djangoenv-sibsirru/lib/python3.14/site-packages')
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
