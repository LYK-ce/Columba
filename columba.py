"""Core Columba email notification implementation."""

from __future__ import annotations

from collections.abc import Iterable
from email.message import EmailMessage
import mimetypes
from pathlib import Path
import smtplib
from typing import Any


class ColumbaSendError(Exception):
    """Raised when sending a notification fails."""


def _normalize_recipients(
    recipients: str | Iterable[str] | None,
) -> list[str]:
    """
    Convert recipient inputs into a clean list of addresses.

    Accepts a single string, any iterable of strings, or None.
    """
    if recipients is None:
        return []
    if isinstance(recipients, str):
        cleaned = recipients.strip()
        return [cleaned] if cleaned else []
    normalized: list[str] = []
    for recipient in recipients:
        if not isinstance(recipient, str):
            continue
        cleaned = recipient.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


class Columba:
    """Simple SMTP email helper supporting attachments and self notification."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        timeout: int = 30,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout

    def send(
        self,
        to: str | list[str],
        subject: str,
        content: str,
        content_type: str = "plain",
        attachments: list[str] | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Send an email based on the configured SMTP server.

        Returns a dict describing the result. Raises ColumbaSendError on failure.
        """
        to_list = _normalize_recipients(to)
        if not to_list:
            raise ColumbaSendError("At least one 'to' recipient must be provided.")

        cc_list = _normalize_recipients(cc)
        bcc_list = _normalize_recipients(bcc)
        attachments = attachments or []

        try:
            message = self._build_message(
                to_list=to_list,
                cc_list=cc_list,
                subject=subject,
                content=content,
                content_type=content_type,
                attachments=attachments,
            )
            refused = self._dispatch(message, to_list + cc_list + bcc_list)
        except Exception as exc:  # pylint: disable=broad-except
            raise ColumbaSendError(f"Failed to send email: {exc}") from exc

        if refused:
            rejected = ", ".join(f"{addr}:{code}" for addr, code in refused.items())
            raise ColumbaSendError(f"Recipients rejected by SMTP server: {rejected}")

        return {
            "success": True,
            "message": "Email sent successfully.",
            "msg_id": message["Message-ID"],
        }

    def send_to_self(
        self,
        subject: str,
        content: str,
        content_type: str = "plain",
        attachments: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send an email to the configured sender account."""
        return self.send(
            to=self.username,
            subject=subject,
            content=content,
            content_type=content_type,
            attachments=attachments,
        )

    def _build_message(
        self,
        *,
        to_list: list[str],
        cc_list: list[str],
        subject: str,
        content: str,
        content_type: str,
        attachments: list[str],
    ) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.username
        message["To"] = ", ".join(to_list)
        if cc_list:
            message["Cc"] = ", ".join(cc_list)

        if content_type.lower() == "html":
            message.add_alternative(content, subtype="html")
        else:
            message.set_content(content, subtype=content_type.lower())

        for attachment in attachments:
            self._add_attachment(message, attachment)

        return message

    def _add_attachment(self, message: EmailMessage, path_str: str) -> None:
        """Attach the given file path to the outgoing message."""
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {path}")
        mime_type, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (
            mime_type.split("/", 1) if mime_type else ("application", "octet-stream")
        )
        with path.open("rb") as handle:
            data = handle.read()
        message.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )

    def _dispatch(
        self,
        message: EmailMessage,
        recipients: list[str],
    ) -> dict[str, tuple[int, bytes]]:
        """Send the message via SMTP and return the refused recipients dict."""
        if not recipients:
            raise ColumbaSendError("Missing recipient list for SMTP dispatch.")

        ClientClass = smtplib.SMTP if self.use_tls else smtplib.SMTP_SSL
        with ClientClass(self.smtp_host, self.smtp_port, timeout=self.timeout) as client:
            if self.use_tls:
                client.starttls()
            client.login(self.username, self.password)
            refused = client.send_message(message, to_addrs=recipients)
        return refused
