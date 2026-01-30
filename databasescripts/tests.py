from django.test import TestCase
from ebay.models import Charity, Item
from ebay.serializers import CharitySerializer

from .database_actions import (
    deleteCharity,
    addCharity,
    itemInDatabase,
    retrieveItem,
    getItemsByCategory,
    deleteItemFromDatabase,
    getItemsBySubCategory,
)

class CharityUtilsTests(TestCase):

    def setUp(self):
        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description = "test charity",
            donation_url = "www.donation.com",
            image_url = "www.picture.com"
        )

    def test_delete_charity_success(self):
        result = deleteCharity(self.charity.id)

        self.assertEqual(result, "Success")
        self.assertFalse(Charity.objects.filter(id=self.charity.id).exists())

    def test_delete_charity_not_found(self):
        result = deleteCharity(9999)

        self.assertIsInstance(result, Exception)

    def test_add_charity_success(self):
        charity_data = {
            "id": 5678,
            "name": "New Charity",
            "description": "new charity",
            "donation_url": "https://donation2.com",
            "image_url": "https://picture2.com"
        }

        result = addCharity(charity_data)

        self.assertEqual(result, "Success")
        self.assertTrue(Charity.objects.filter(name="New Charity").exists())

    def test_add_charity_failure(self):
        charity_data = {}

        result = addCharity(charity_data)

        self.assertEqual(result, "Failure")


class ItemLookupTests(TestCase):

    def setUp(self):

        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description = "test charity",
            donation_url = "www.donation.com",
            image_url = "www.picture.com"
        )

        self.item = Item.objects.create(
            ebay_id="ABC123",
            category=1,
            category_list=[{"categoryName": "Books"}],
            price=9.99,
            charity=self.charity
        )

    def test_item_in_database_true(self):
        result = itemInDatabase("ABC123")
        self.assertTrue(result)

    def test_item_in_database_false(self):
        result = itemInDatabase("NOT_THERE")
        self.assertFalse(result)

    def test_retrieve_item_success(self):
        item = retrieveItem("ABC123")

        self.assertIsNotNone(item)
        self.assertEqual(item.ebay_id, "ABC123")

    def test_retrieve_item_not_found(self):
        item = retrieveItem("MISSING")

        self.assertIsNone(item)

class ItemQueryTests(TestCase):

    def setUp(self):

        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description = "test charity",
            donation_url = "www.donation.com",
            image_url = "www.picture.com"
        )

        self.item1 = Item.objects.create(
            ebay_id="ITEM1",
            category=1,
            category_list=[{"categoryName": "Electronics"}],
            price=9.99,
            charity=self.charity
        )

        self.item2 = Item.objects.create(
            ebay_id="ITEM2",
            category=2,
            category_list=[{"categoryName": "Books"}],
            price=9.99,
            charity=self.charity
        )

    def test_get_items_by_category(self):
        items = getItemsByCategory(1)

        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().ebay_id, "ITEM1")

    def test_get_items_by_category_empty(self):
        items = getItemsByCategory(999)

        self.assertEqual(items.count(), 0)

    def test_get_items_by_subcategory_success(self):
        items = getItemsBySubCategory("Books")

        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().ebay_id, "ITEM2")

    def test_get_items_by_subcategory_no_match(self):
        items = getItemsBySubCategory("Toys")

        self.assertEqual(items.count(), 0)

class ItemDeleteTests(TestCase):

    def setUp(self):

        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description = "test charity",
            donation_url = "www.donation.com",
            image_url = "www.picture.com"
        )

        self.item = Item.objects.create(
            ebay_id="DELETE_ME",
            category=1,
            category_list=[{"categoryName": "Misc"}],
            price=9.99,
            charity=self.charity
        )

    def test_delete_item_success(self):
        result = deleteItemFromDatabase("DELETE_ME")

        self.assertEqual(result, "Success")
        self.assertFalse(Item.objects.filter(ebay_id="DELETE_ME").exists())

    def test_delete_item_not_found(self):
        result = deleteItemFromDatabase("MISSING")

        self.assertEqual(result, "Failure")