import os
import sys


site_user_root_dir = "/home/d/dpitstudio/sibsir.ru/public_html"
sys.path.insert(0, site_user_root_dir + "/mysite")
sys.path.insert(1, site_user_root_dir + "/venv/lib64/python3.14/site-packages")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
