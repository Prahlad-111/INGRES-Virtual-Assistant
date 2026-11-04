import os
import unittest
from unittest.mock import Mock, patch

import requests

from services.email_service import send_otp_email


class SendOtpEmailTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "BREVO_API_KEY": "test-api-key",
            "BREVO_SENDER_EMAIL": "verified@example.com",
            "BREVO_SENDER_NAME": "INGRES AI",
        },
        clear=True,
    )
    @patch("services.email_service.requests.post")
    def test_sends_password_reset_email_through_brevo_api(self, post):
        response = Mock()
        post.return_value = response

        self.assertTrue(
            send_otp_email(
                "user@example.com",
                "123456",
                purpose="password_reset",
            )
        )

        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(
            args[0],
            "https://api.brevo.com/v3/smtp/email",
        )
        self.assertEqual(kwargs["headers"]["api-key"], "test-api-key")
        self.assertEqual(
            kwargs["json"]["sender"]["email"],
            "verified@example.com",
        )
        self.assertEqual(
            kwargs["json"]["to"],
            [{"email": "user@example.com"}],
        )
        self.assertEqual(
            kwargs["json"]["subject"],
            "INGRES AI - Password Reset OTP",
        )
        response.raise_for_status.assert_called_once_with()

    @patch.dict(
        os.environ,
        {
            "BREVO_API_KEY": "test-api-key",
            "BREVO_SENDER_EMAIL": "verified@example.com",
        },
        clear=True,
    )
    @patch("services.email_service.requests.post")
    def test_raises_when_brevo_api_rejects_email(self, post):
        response = Mock()
        response.status_code = 401
        post.return_value.raise_for_status.side_effect = (
            requests.HTTPError(response=response)
        )

        with self.assertRaisesRegex(RuntimeError, "Unable to send OTP email"):
            send_otp_email("user@example.com", "123456")

    @patch.dict(os.environ, {}, clear=True)
    def test_requires_api_key_and_sender_email(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "Brevo API configuration is incomplete",
        ):
            send_otp_email("user@example.com", "123456")


if __name__ == "__main__":
    unittest.main()
