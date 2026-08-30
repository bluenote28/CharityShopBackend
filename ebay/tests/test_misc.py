import unittest

from ebay import admin, constants
from ebay.apps import EbayConfig
from ebay.urls import charity_urls, item_urls, report_urls, user_urls


class TestAppModulesImport(unittest.TestCase):

    def test_admin_module_imports(self):
        self.assertTrue(hasattr(admin, "admin"))

    def test_constants_has_filter_options(self):
        self.assertIn("Books", constants.FILTER_OPTIONS)
        self.assertEqual(constants.FILTER_OPTIONS["DVD"][0], "DVDs & Blu-ray Discs")

    def test_url_modules_expose_urlpatterns(self):
        self.assertTrue(charity_urls.urlpatterns)
        self.assertTrue(item_urls.urlpatterns)
        self.assertTrue(report_urls.urlpatterns)
        self.assertTrue(user_urls.urlpatterns)

    def test_ebay_config_name(self):
        self.assertEqual(EbayConfig.name, "ebay")
