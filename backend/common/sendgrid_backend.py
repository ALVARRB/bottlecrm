import logging

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

import requests

logger = logging.getLogger(__name__)
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


class SendGridEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, "SENDGRID_API_KEY", "")

    def send_messages(self, email_messages):
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not set — email not sent")
            return 0
        count = 0
        for message in email_messages:
            try:
                self._send_one(message)
                count += 1
            except Exception as e:
                logger.exception("SendGrid email failed: %s", e)
                if not self.fail_silently:
                    raise
        return count

    def _send_one(self, message):
        content = []
        if message.body:
            subtype = message.content_subtype or "plain"
            content.append({"type": f"text/{subtype}", "value": message.body})

        to_list = [{"email": addr} for addr in message.to] if message.to else []
        personalization = {"to": to_list}
        if message.cc:
            personalization["cc"] = [{"email": addr} for addr in message.cc]
        if message.bcc:
            personalization["bcc"] = [{"email": addr} for addr in message.bcc]

        payload = {
            "personalizations": [personalization],
            "from": {"email": message.from_email},
            "subject": message.subject or "",
            "content": content,
        }
        if hasattr(message, "reply_to") and message.reply_to:
            payload["reply_to"] = {"email": message.reply_to[0]}

        resp = requests.post(
            SENDGRID_API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        if resp.status_code not in (200, 201, 202):
            body = resp.text[:500]
            logger.error(
                "SendGrid API error: %s %s — %s",
                resp.status_code,
                resp.reason,
                body,
            )
            resp.raise_for_status()
