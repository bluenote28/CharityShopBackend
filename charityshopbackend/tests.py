import os
import sys
from unittest import TestCase, main, mock
import importlib

class TestASGIBasic(TestCase):

    def test_environment_variable_set(self):
        from charityshopbackend import asgi
        
        self.assertEqual(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            'charityshopbackend.settings'
        )

    def test_application_exists(self):
        from charityshopbackend.asgi import application
        
        self.assertIsNotNone(application)

    def test_application_callable(self):
        from charityshopbackend.asgi import application
        
        self.assertTrue(callable(application))

    def test_application_type(self):
        from django.core.handlers.asgi import ASGIHandler
        from charityshopbackend.asgi import application
        
        self.assertIsInstance(application, ASGIHandler)


class TestWSGIConfiguration(TestCase):

    def test_django_settings_module_is_set(self):
        from charityshopbackend import wsgi
        
        self.assertEqual(
            os.environ.get('DJANGO_SETTINGS_MODULE'),
            'charityshopbackend.settings'
        )

    def test_application_is_not_none(self):
        from charityshopbackend.wsgi import application
        
        self.assertIsNotNone(application)

    def test_application_is_callable(self):
        from charityshopbackend.wsgi import application
        
        self.assertTrue(callable(application))

    def test_application_has_call_method(self):
        from charityshopbackend.wsgi import application
        
        self.assertTrue(hasattr(application, '__call__'))

    def test_application_is_wsgi_handler(self):
        from django.core.handlers.wsgi import WSGIHandler
        from charityshopbackend.wsgi import application
        
        self.assertIsInstance(application, WSGIHandler)

    def test_module_can_be_imported(self):
        try:
            from charityshopbackend import wsgi
            self.assertIsNotNone(wsgi)
        except ImportError as e:
            self.fail(f"Failed to import wsgi module: {e}")

    def test_application_exported(self):
        from charityshopbackend import wsgi
        
        self.assertTrue(hasattr(wsgi, 'application'))

    @mock.patch('django.core.wsgi.get_wsgi_application')
    def test_get_wsgi_application_called(self, mock_get_wsgi):
        mock_get_wsgi.return_value = mock.Mock()
        
        import charityshopbackend.wsgi
        importlib.reload(charityshopbackend.wsgi)
        
        mock_get_wsgi.assert_called()