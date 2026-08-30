import unittest
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User as DjangoUser

from databasescripts.refresh_database import deleteInactiveItems, refreshDatabase
from databasescripts.views import RefreshDatabaseView


class TestDeleteInactiveItems(unittest.TestCase):

    @patch("ebay.ebay_client.EbayClient")
    def test_keeps_active_items(self, mock_client_class):
        mock_client_class.return_value.isItemActive.return_value = True
        item = Mock(ebay_id="keep")

        with patch("databasescripts.database_actions.deleteItemFromDatabase") as mock_delete:
            deleteInactiveItems([item])

        mock_delete.assert_not_called()

    @patch("ebay.ebay_client.EbayClient")
    def test_deletes_inactive_and_error_items(self, mock_client_class):
        mock_client_class.return_value.isItemActive.side_effect = [False, "error"]
        inactive = Mock(ebay_id="gone")
        errored = Mock(ebay_id="err")

        with patch("databasescripts.database_actions.deleteItemFromDatabase") as mock_delete:
            deleteInactiveItems([inactive, errored])

        mock_delete.assert_any_call("gone")
        mock_delete.assert_any_call("err")
        self.assertEqual(mock_delete.call_count, 2)

    @patch("ebay.ebay_client.EbayClient")
    def test_logs_when_loop_raises(self, mock_client_class):
        mock_client_class.return_value.isItemActive.side_effect = Exception("boom")

        deleteInactiveItems([Mock(ebay_id="x")])


class TestRefreshDatabase(unittest.TestCase):

    @patch("databasescripts.refresh_database.deleteInactiveItems")
    def test_refreshes_single_charity(self, mock_delete_inactive):
        favorite_item = Mock(id=9)
        favorite_list = Mock()
        favorite_list.items.all.return_value = [favorite_item]

        charity_items = Mock()
        loader = Mock()

        with patch("ebay.models.FavoriteList") as mock_fav, \
             patch("ebay.models.Item") as mock_item, \
             patch("ebay.models.Charity"), \
             patch("ebay.load_data_to_db.DatabaseLoader", return_value=loader), \
             patch("databasescripts.database_actions.updateCharityUpdatedAt") as mock_update:
            mock_fav.objects.filter.return_value = [favorite_list]
            mock_item.objects.filter.return_value.exclude.return_value = charity_items

            refreshDatabase(42)

        mock_delete_inactive.assert_called_once()
        charity_items.delete.assert_called_once()
        loader.load_items_to_db.assert_called_once()
        mock_update.assert_called_once_with(42)

    @patch("databasescripts.refresh_database.deleteInactiveItems")
    def test_refreshes_all_charities_when_id_is_none(self, mock_delete_inactive):
        favorite_item = Mock(id=3)
        favorite_list = Mock()
        favorite_list.items.all.return_value = [favorite_item]
        charity = Mock(id=7, name="All Goods")
        loader = Mock()
        charity_items = Mock()

        with patch("ebay.models.FavoriteList") as mock_fav, \
             patch("ebay.models.Item") as mock_item, \
             patch("ebay.models.Charity") as mock_charity, \
             patch("ebay.load_data_to_db.DatabaseLoader", return_value=loader), \
             patch("databasescripts.database_actions.updateCharityUpdatedAt") as mock_update:
            mock_fav.objects.filter.return_value = [favorite_list]
            mock_charity.objects.all.return_value = [charity]
            mock_item.objects.filter.return_value.exclude.return_value = charity_items

            refreshDatabase(None)

        mock_delete_inactive.assert_called_once()
        charity_items.delete.assert_called_once()
        loader.load_items_to_db.assert_called_once()
        mock_update.assert_called_once_with(7)


class TestRefreshDatabaseView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = RefreshDatabaseView.as_view()
        self.admin = Mock(spec=DjangoUser)
        self.admin.is_authenticated = True
        self.admin.is_staff = True

    @patch("databasescripts.views.disk")
    @patch("databasescripts.views.Queue")
    @patch("databasescripts.views.get_redis")
    @patch("databasescripts.views.close_old_connections")
    def test_post_enqueues_refresh_for_charity(self, mock_close, mock_redis, mock_queue, mock_disk):
        queue = Mock()
        mock_queue.return_value = queue

        request = self.factory.post("/api/refresh_items/", {"id": 5}, format="json")
        force_authenticate(request, user=self.admin)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "success")
        queue.enqueue.assert_called_once()
        self.assertEqual(queue.enqueue.call_args.args[0], refreshDatabase)
        self.assertEqual(queue.enqueue.call_args.args[1], 5)
        mock_disk.clear.assert_called_once()

    @patch("databasescripts.views.disk")
    @patch("databasescripts.views.Queue")
    @patch("databasescripts.views.get_redis")
    @patch("databasescripts.views.close_old_connections")
    def test_get_enqueues_full_refresh(self, mock_close, mock_redis, mock_queue, mock_disk):
        queue = Mock()
        mock_queue.return_value = queue

        request = self.factory.get("/api/refresh_items/")
        force_authenticate(request, user=self.admin)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        queue.enqueue.assert_called_once()
        self.assertEqual(queue.enqueue.call_args.args[0], refreshDatabase)
        mock_disk.clear.assert_called_once()

    def test_unauthenticated_is_rejected(self):
        request = self.factory.get("/api/refresh_items/")
        response = self.view(request)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
