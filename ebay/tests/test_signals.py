from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings

from ebay.signals import registeredUser, updateUser


class UpdateUserSignalTests(TestCase):

    def test_sets_username_to_email_when_email_present(self):
        user = User(username="oldname", email="new@example.com")
        updateUser(sender=User, instance=user)
        self.assertEqual(user.username, "new@example.com")

    def test_leaves_username_when_email_empty(self):
        user = User(username="keepme", email="")
        updateUser(sender=User, instance=user)
        self.assertEqual(user.username, "keepme")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_pre_save_updates_username_on_create(self):
        user = User.objects.create_user(
            username="placeholder",
            email="real@example.com",
            password="pass1234",
        )
        user.refresh_from_db()
        self.assertEqual(user.username, "real@example.com")


class RegisteredUserSignalTests(TestCase):

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="charityshopusa@yahoo.com",
    )
    def test_sends_welcome_email_when_user_created(self):
        User.objects.create_user(
            username="welcome@example.com",
            email="welcome@example.com",
            password="pass1234",
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Welcome to The charity Shop")
        self.assertEqual(mail.outbox[0].to, ["welcome@example.com"])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_does_not_send_email_on_update(self):
        user = User.objects.create_user(
            username="keep@example.com",
            email="keep@example.com",
            password="pass1234",
        )
        mail.outbox.clear()

        user.first_name = "Updated"
        user.save()

        self.assertEqual(len(mail.outbox), 0)

    @patch("ebay.signals.send_mail", side_effect=Exception("smtp down"))
    def test_email_failure_is_caught(self, mock_send):
        user = User(email="fail@example.com")
        registeredUser(sender=User, instance=user, created=True)
        mock_send.assert_called_once()
