from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Product


class AuthRoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("member1", password="secret6")
        self.staff = User.objects.create_user("staff1", password="secret6", is_staff=True)

    def test_register_login_logout(self):
        resp = self.client.post(reverse("register"), {
            "username": "newuser",
            "email": "n@n.com",
            "password1": "secret6",
            "password2": "secret6",
        })
        self.assertEqual(resp.status_code, 302)
        resp = self.client.post(reverse("login"), {
            "username": "newuser",
            "password": "secret6",
        })
        self.assertIn(resp.status_code, (200, 302))

    def test_dashboard_access_control(self):
        self.client.login(username="member1", password="secret6")
        resp = self.client.get(reverse("dashboard"))
        self.assertIn(resp.status_code, (302, 403))

        self.client.login(username="staff1", password="secret6")
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 200)


class ProductCrudTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user("staff1", password="secret6", is_staff=True)
        self.client.login(username="staff1", password="secret6")
        self.product = Product.objects.create(name="Toy A", price=100, stock=5)

    def test_create_product(self):
        resp = self.client.post(reverse("add_product"), {
            "name": "Toy B",
            "price": "200",
            "stock": "3",
            "is_active": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Product.objects.filter(name="Toy B").exists())

    def test_edit_product(self):
        resp = self.client.post(reverse("edit_product", args=[self.product.pk]), {
            "name": "Toy A edited",
            "price": "150",
            "stock": "2",
            "is_active": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Toy A edited")

    def test_delete_product(self):
        resp = self.client.get(reverse("delete_product", args=[self.product.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())


class SearchPaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        staff = User.objects.create_user("staff1", password="secret6", is_staff=True)
        self.client.login(username="staff1", password="secret6")
        for i in range(12):
            Product.objects.create(name=f"Toy {i}", price=10 + i, stock=1)

    def test_search(self):
        resp = self.client.get(reverse("dashboard"), {"pq": "Toy 1"})
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("Toy 1", content)

    def test_pagination(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("pagination", resp.content.decode())