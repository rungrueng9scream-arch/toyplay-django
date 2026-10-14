from decimal import Decimal

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import (
    Product,
    Category,
    Review,
    Wishlist,
    Coupon,
    Cart,
    CartItem,
    Order,
)


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

    def test_stats_visible(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "ยอดขายรวม")


class CategoryFilterTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name="หุ่นยนต์ทดสอบ")
        self.in_cat = Product.objects.create(name="InCat Toy", price=10, stock=1, category=self.cat)
        self.out_cat = Product.objects.create(name="OutCat Toy", price=20, stock=1)

    def test_filter_by_category(self):
        resp = self.client.get(reverse("product"), {"category": self.cat.id})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "InCat Toy")
        self.assertNotContains(resp, "OutCat Toy")

    def test_sort_by_price(self):
        resp = self.client.get(reverse("product"), {"sort": "price_asc"})
        content = resp.content.decode()
        self.assertLess(content.index("InCat Toy"), content.index("OutCat Toy"))

    def test_add_category_staff_only(self):
        staff = User.objects.create_user("staffcat", password="secret6", is_staff=True)
        self.client.login(username="staffcat", password="secret6")
        self.client.post(reverse("add_category"), {"name": "หมวดใหม่"})
        self.assertTrue(Category.objects.filter(name="หมวดใหม่").exists())


class ReviewWishlistTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("reviewer", password="secret6")
        self.client.login(username="reviewer", password="secret6")
        self.product = Product.objects.create(name="Review Toy", price=50, stock=2)

    def test_product_detail_page(self):
        resp = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Review Toy")

    def test_add_and_update_review(self):
        self.client.post(reverse("review_add", args=[self.product.pk]), {"rating": "5", "comment": "ดีมาก"})
        self.assertTrue(Review.objects.filter(product=self.product, user=self.user, rating=5).exists())

        self.client.post(reverse("review_add", args=[self.product.pk]), {"rating": "3", "comment": "ปรับปรุง"})
        self.assertEqual(Review.objects.filter(product=self.product, user=self.user).count(), 1)
        review = Review.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.rating, 3)

    def test_wishlist_toggle(self):
        self.client.get(reverse("wishlist_toggle", args=[self.product.pk]))
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product).exists())

        self.client.get(reverse("wishlist_toggle", args=[self.product.pk]))
        self.assertFalse(Wishlist.objects.filter(user=self.user, product=self.product).exists())

    def test_wishlist_page(self):
        Wishlist.objects.create(user=self.user, product=self.product)
        resp = self.client.get(reverse("wishlist"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Review Toy")


class CheckoutCouponStockTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("buyer", password="secret6")
        self.client.login(username="buyer", password="secret6")
        self.product = Product.objects.create(name="Buy Toy", price=100, stock=3)
        self.coupon = Coupon.objects.create(code="SAVE10", discount_percent=10)

    def _cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.user)
        return cart

    def test_checkout_decrements_stock_and_applies_coupon(self):
        CartItem.objects.create(cart=self._cart(), product=self.product, quantity=2)
        resp = self.client.post(reverse("checkout"), {"coupon_code": "save10"})
        self.assertEqual(resp.status_code, 302)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.discount_amount, Decimal("20.00"))
        self.assertEqual(order.total_price, Decimal("180.00"))

        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.used_count, 1)
        self.assertFalse(CartItem.objects.filter(cart=self._cart()).exists())

    def test_checkout_blocks_when_stock_insufficient(self):
        CartItem.objects.create(cart=self._cart(), product=self.product, quantity=5)
        resp = self.client.post(reverse("checkout"))
        self.assertEqual(resp.status_code, 302)

        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_cart_add_blocks_out_of_stock(self):
        sold_out = Product.objects.create(name="Sold Out", price=10, stock=0)
        self.client.post(reverse("cart_add", args=[sold_out.pk]))
        self.assertFalse(CartItem.objects.filter(product=sold_out).exists())