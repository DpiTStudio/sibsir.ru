from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import UserProfile
from accounts.admin import UserProfileAdmin
from django.contrib.admin.sites import AdminSite


class UserProfileAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = UserProfileAdmin(UserProfile, self.site)
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="super_test",
            email="super@example.com",
            password="Password123!"
        )

    def test_wholesale_price_tools_on_unsaved_obj(self):
        unsaved_profile = UserProfile()
        # Should not throw NoReverseMatch when id is None
        result = self.admin.wholesale_price_tools(unsaved_profile)
        self.assertIn("доступны после сохранения", str(result))

    def test_price_list_send_btn_on_unsaved_obj(self):
        unsaved_profile = UserProfile()
        result = self.admin.price_list_send_btn(unsaved_profile)
        self.assertIn("—", str(result))

    def test_admin_add_userprofile_view(self):
        self.client.force_login(self.superuser)
        res = self.client.get(reverse("admin:accounts_userprofile_add"), HTTP_HOST="127.0.0.1")
        self.assertEqual(res.status_code, 200)
