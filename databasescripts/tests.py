from unittest.mock import Mock, patch

from django.test import TestCase
from ebay.models import Charity, Item

from .database_actions import (
    addCharity,
    deleteCharity,
    deleteItemFromDatabase,
    getItemsByCategory,
    getItemsByFilter,
    getItemsBySubCategory,
    itemInDatabase,
    retrieveItem,
    updateCharityUpdatedAt,
)


def _create_item(charity, ebay_id, category=1, category_name="Books", name=None):
    return Item.objects.create(
        ebay_id=ebay_id,
        name=name or ebay_id,
        web_url=f"https://ebay.com/{ebay_id}",
        category=category,
        category_list=[{"categoryName": category_name}],
        price="9.99",
        charity=charity,
    )


class CharityUtilsTests(TestCase):

    def setUp(self):
        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description="test charity",
            donation_url="https://donation.com",
            image_url="https://picture.com",
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
            "image_url": "https://picture2.com",
        }

        result = addCharity(charity_data)

        self.assertEqual(result, "Success")
        self.assertTrue(Charity.objects.filter(name="New Charity").exists())

    def test_add_charity_failure(self):
        result = addCharity({})

        self.assertEqual(result, "Failure")


class ItemLookupTests(TestCase):

    def setUp(self):
        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description="test charity",
            donation_url="https://donation.com",
            image_url="https://picture.com",
        )
        self.item = _create_item(self.charity, "ABC123")

    def test_item_in_database_true(self):
        self.assertTrue(itemInDatabase("ABC123"))

    def test_item_in_database_false(self):
        self.assertFalse(itemInDatabase("NOT_THERE"))

    @patch("databasescripts.database_actions.Item.objects.get", side_effect=Exception("db down"))
    def test_item_in_database_other_exception(self, mock_get):
        self.assertIsNone(itemInDatabase("ABC123"))

    def test_retrieve_item_success(self):
        item = retrieveItem("ABC123")

        self.assertIsNotNone(item)
        self.assertEqual(item.ebay_id, "ABC123")

    def test_retrieve_item_not_found(self):
        self.assertIsNone(retrieveItem("MISSING"))

    @patch("databasescripts.database_actions.Item.objects.get", side_effect=Exception("db down"))
    def test_retrieve_item_other_exception(self, mock_get):
        self.assertIsNone(retrieveItem("ABC123"))


class ItemQueryTests(TestCase):

    def setUp(self):
        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description="test charity",
            donation_url="https://donation.com",
            image_url="https://picture.com",
        )
        self.item1 = _create_item(self.charity, "ITEM1", category=1, category_name="Electronics")
        self.item2 = _create_item(self.charity, "ITEM2", category=2, category_name="Books")

    def test_get_items_by_category(self):
        items = getItemsByCategory(1)

        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().ebay_id, "ITEM1")

    def test_get_items_by_category_empty(self):
        self.assertEqual(getItemsByCategory(999).count(), 0)

    @patch("databasescripts.database_actions.Item.objects.filter", side_effect=Exception("db down"))
    def test_get_items_by_category_error(self, mock_filter):
        self.assertEqual(getItemsByCategory(1), [])

    @patch("databasescripts.database_actions.Item.objects.filter")
    def test_get_items_by_subcategory_success(self, mock_filter):
        mock_filter.return_value = [self.item2]

        items = getItemsBySubCategory("Books")

        mock_filter.assert_called_once_with(category_list__contains=[{"categoryName": "Books"}])
        self.assertEqual(items, [self.item2])

    @patch("databasescripts.database_actions.Item.objects.filter")
    def test_get_items_by_subcategory_no_match(self, mock_filter):
        mock_filter.return_value = Item.objects.none()

        items = getItemsBySubCategory("Toys")

        self.assertEqual(items.count(), 0)

    @patch("databasescripts.database_actions.Item.objects.filter", side_effect=Exception("db down"))
    def test_get_items_by_subcategory_error(self, mock_filter):
        self.assertEqual(getItemsBySubCategory("Books"), "Failure")

    @patch("databasescripts.database_actions.Item.objects.filter")
    def test_get_items_by_filter(self, mock_filter):
        filtered = Mock()
        mock_filter.return_value.filter.return_value = [self.item2]

        items = getItemsByFilter("Books", "ITEM")

        mock_filter.assert_called_once_with(category_list__contains=[{"categoryName": "Books"}])
        mock_filter.return_value.filter.assert_called_once_with(name__icontains="ITEM")
        self.assertEqual(items, [self.item2])

    @patch("databasescripts.database_actions.Item.objects.filter", side_effect=Exception("db down"))
    def test_get_items_by_filter_error(self, mock_filter):
        self.assertEqual(getItemsByFilter("Books", "ITEM"), "Failure")


class ItemDeleteTests(TestCase):

    def setUp(self):
        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description="test charity",
            donation_url="https://donation.com",
            image_url="https://picture.com",
        )
        self.item = _create_item(self.charity, "DELETE_ME", category_name="Misc")

    def test_delete_item_success(self):
        result = deleteItemFromDatabase("DELETE_ME")

        self.assertEqual(result, "Success")
        self.assertFalse(Item.objects.filter(ebay_id="DELETE_ME").exists())

    def test_delete_item_not_found(self):
        self.assertEqual(deleteItemFromDatabase("MISSING"), "Failure")


class UpdateCharityUpdatedAtTests(TestCase):

    def setUp(self):
        self.charity = Charity.objects.create(
            id=1234,
            name="Test Charity",
            description="test charity",
            donation_url="https://donation.com",
            image_url="https://picture.com",
        )

    def test_updates_timestamp(self):
        previous = self.charity.updated_at

        updateCharityUpdatedAt(self.charity.id)

        self.charity.refresh_from_db()
        self.assertIsNotNone(self.charity.updated_at)
        self.assertGreaterEqual(self.charity.updated_at, previous)
