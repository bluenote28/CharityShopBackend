from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from ebay.models import Charity, Purchase
from ebay.views.purchase_views import PurchaseView


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PurchaseViewTests(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = PurchaseView.as_view()
        self.user = User.objects.create_user(
            username="buyer@example.com",
            email="buyer@example.com",
            password="pass1234",
        )
        self.other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="pass1234",
        )
        self.charity = Charity.objects.create(
            id=1,
            name="Good Cause",
            description="helps people",
        )
        self.purchase_payload = {
            "item_name": "Vintage Lamp",
            "amount": "25.00",
            "donation_percentage": "10.0",
            "charity": self.charity.id,
            "purchased_at": "2026-08-30",
        }

    def test_get_returns_purchases_for_authenticated_user(self):
        Purchase.objects.create(
            user=self.user,
            item_name="Vintage Lamp",
            amount="25.00",
            donation_percentage="10.0",
            charity=self.charity,
            purchased_at="2026-08-30",
        )
        Purchase.objects.create(
            user=self.other_user,
            item_name="Other Item",
            amount="5.00",
            donation_percentage="15.0",
            charity=self.charity,
            purchased_at="2026-08-29",
        )

        request = self.factory.get("/api/purchases/")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["item_name"], "Vintage Lamp")
        self.assertEqual(response.data[0]["charity_name"], "Good Cause")

    def test_get_returns_purchases_for_particular_user(self):
        Purchase.objects.create(
            user=self.other_user,
            item_name="Other Item",
            amount="5.00",
            donation_percentage="15.0",
            charity=self.charity,
            purchased_at="2026-08-29",
        )

        request = self.factory.get(f"/api/purchases/{self.other_user.id}/")
        force_authenticate(request, user=self.user)
        response = self.view(request, user_id=self.other_user.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["item_name"], "Other Item")
        self.assertEqual(response.data[0]["user"], self.other_user.id)

    def test_post_records_purchase_and_returns_that_users_purchases(self):
        request = self.factory.post("/api/purchases/", self.purchase_payload, format="json")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Purchase.objects.filter(user=self.user).count(), 1)
        self.assertEqual(response.data[0]["item_name"], "Vintage Lamp")
        self.assertEqual(response.data[0]["user"], self.user.id)
        self.assertEqual(response.data[0]["charity_name"], "Good Cause")

    def test_post_ignores_user_in_payload(self):
        payload = {**self.purchase_payload, "user": self.other_user.id}

        request = self.factory.post("/api/purchases/", payload, format="json")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        purchase = Purchase.objects.get()
        self.assertEqual(purchase.user_id, self.user.id)

    def test_post_returns_400_for_invalid_payload(self):
        request = self.factory.post("/api/purchases/", {"item_name": "Missing fields"}, format="json")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Purchase.objects.count(), 0)
