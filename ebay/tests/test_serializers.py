from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from ebay.models import Charity, FavoriteList, Item
from ebay.serializers import (
    CharitySerializer,
    FavoriteListSerializer,
    ItemSerializer,
    UserSerializer,
    UserSerializerWithToken,
)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tester@example.com",
            email="tester@example.com",
            password="pass1234",
            first_name="Test",
            last_name="User",
            is_staff=True,
        )
        self.charity = Charity.objects.create(
            id=1,
            name="Good Cause",
            description="helps people",
            donation_url="https://donate.example.com",
            image_url="https://img.example.com/c.png",
        )
        self.item = Item.objects.create(
            ebay_id="ITEM1",
            name="Vintage Lamp",
            web_url="https://ebay.com/item1",
            price="12.50",
            charity=self.charity,
            category="Home",
        )
        self.favorite_list = FavoriteList.objects.create(user=self.user)
        self.favorite_list.items.add(self.item)
        self.favorite_list.charities.add(self.charity)

    def test_charity_serializer_includes_name(self):
        data = CharitySerializer(self.charity).data
        self.assertEqual(data["name"], "Good Cause")
        self.assertEqual(data["id"], 1)

    def test_item_serializer_includes_ebay_id(self):
        data = ItemSerializer(self.item).data
        self.assertEqual(data["ebay_id"], "ITEM1")
        self.assertEqual(data["name"], "Vintage Lamp")

    def test_favorite_list_nests_items_and_charities(self):
        data = FavoriteListSerializer(self.favorite_list).data
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(len(data["charities"]), 1)
        self.assertEqual(data["items"][0]["ebay_id"], "ITEM1")

    def test_user_serializer_computed_fields(self):
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["isAdmin"], True)
        self.assertEqual(data["name"], "Test User")
        self.assertEqual(data["email"], "tester@example.com")
        self.assertEqual(data["username"], "tester@example.com")
        self.assertEqual(serializer.get_email(self.user), "tester@example.com")
        self.assertEqual(serializer.get_username(self.user), "tester@example.com")

    def test_user_serializer_with_token_includes_tokens(self):
        data = UserSerializerWithToken(self.user).data
        self.assertTrue(data["token"])
        self.assertTrue(data["refresh"])

    def test_model_str_methods(self):
        self.assertEqual(str(self.charity), "Good Cause")
        self.assertEqual(str(self.item), "Vintage Lamp")
        self.assertEqual(str(self.favorite_list), f"FavoriteList of User {self.user.id}")
