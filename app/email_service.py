"""Email service for sending emails via SMTP."""

import imaplib
import json
import logging
import os
import re
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Practical RFC 5322 compliant email regex
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
)

# Connection timeout in seconds
SMTP_TIMEOUT = 30


def get_config_path() -> Path:
    """Get config.json path relative to this module."""
    return Path(__file__).parent.parent / "config.json"


def load_config() -> dict[str, Any]:
    """
    Load SMTP configuration from environment variables or config.json.

    Environment variables take precedence over config.json.

    Environment variables:
        SMTP_HOST: SMTP server hostname
        SMTP_PORT: SMTP port (default: 465)
        SMTP_USE_TLS: "true" for STARTTLS, "false" for SSL (default: "false")
        SMTP_USERNAME: SMTP username/email
        SMTP_PASSWORD: SMTP password

    Returns:
        Dictionary with validated configuration.

    Raises:
        FileNotFoundError: If config.json doesn't exist and env vars not set.
        json.JSONDecodeError: If config.json is invalid JSON.
        KeyError: If required fields are missing.
    """
    # Check if environment variables are set
    if os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USERNAME"):
        logger.info("Loading configuration from environment variables")
        config = {
            "smtp_host": os.environ["SMTP_HOST"],
            "smtp_port": int(os.environ.get("SMTP_PORT", "465")),
            "smtp_use_tls": os.environ.get("SMTP_USE_TLS", "false").lower() == "true",
            "username": os.environ["SMTP_USERNAME"],
            "password": os.environ.get("SMTP_PASSWORD", ""),
            # IMAP settings for saving to Sent folder
            "imap_host": os.environ.get("IMAP_HOST", os.environ["SMTP_HOST"]),
            "imap_port": int(os.environ.get("IMAP_PORT", "993")),
            "save_to_sent": os.environ.get("SAVE_TO_SENT", "true").lower() == "true",
            "sent_folder": os.environ.get("SENT_FOLDER", "Sent"),
        }
        return config

    # Fall back to config.json
    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(
            f"config.json not found at {config_path} and environment variables not set. "
            "Either set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD environment variables, "
            "or copy config.json.example to config.json and edit it."
        )

    logger.info(f"Loading configuration from {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Validate required fields
    required_fields = ["smtp_host", "smtp_port", "smtp_use_tls", "username", "password"]
    for field in required_fields:
        if field not in config:
            raise KeyError(f"Missing required field: {field}")

    return config


def is_valid_email(email: str) -> bool:
    """
    Check if a single email address is valid.

    Args:
        email: Email address to validate.

    Returns:
        True if valid, False otherwise.
    """
    return EMAIL_PATTERN.match(email.strip()) is not None


def parse_email_list(emails: str) -> list[str]:
    """
    Parse a comma-separated string of emails into a list.

    Args:
        emails: Comma-separated email addresses.

    Returns:
        List of stripped email addresses (empty strings removed).
    """
    return [e.strip() for e in emails.split(",") if e.strip()]


def validate_emails(emails: list[str]) -> None:
    """
    Validate a list of email addresses.

    Args:
        emails: List of email addresses to validate.

    Raises:
        ValueError: If any email address is invalid.
    """
    for email in emails:
        if not is_valid_email(email):
            raise ValueError(f"'{email}' is not a valid email address")


def save_to_sent_folder(config: dict[str, Any], msg_string: str) -> None:
    """
    Save a copy of the sent email to the Sent folder via IMAP.

    Args:
        config: Configuration dictionary with IMAP settings.
        msg_string: The email message as a string.

    Raises:
        imaplib.IMAP4.error: On any IMAP error.
    """
    imap_host = config.get("imap_host", config["smtp_host"])
    imap_port = config.get("imap_port", 993)
    sent_folder = config.get("sent_folder", "Sent")

    logger.info(f"Connecting to IMAP server {imap_host}:{imap_port}")

    imap = None
    try:
        # Connect via SSL (port 993)
        imap = imaplib.IMAP4_SSL(imap_host, imap_port)
        imap.login(config["username"], config["password"])

        # Append to Sent folder with \Seen flag
        # The date must be timezone-aware for Time2Internaldate
        imap.append(
            sent_folder,
            "\\Seen",
            imaplib.Time2Internaldate(datetime.now(timezone.utc)),
            msg_string.encode("utf-8"),
        )
        logger.info(f"Email saved to {sent_folder} folder")

    finally:
        if imap:
            try:
                imap.logout()
            except Exception:
                pass  # Ignore errors during cleanup


def send_email_smtp(
    config: dict[str, Any],
    to_list: list[str],
    cc_list: list[str],
    subject: str,
    body: str,
) -> None:
    """
    Send email via SMTP and optionally save to Sent folder via IMAP.

    Args:
        config: SMTP configuration dictionary.
        to_list: List of recipient email addresses.
        cc_list: List of CC email addresses.
        subject: Email subject.
        body: Plain text body.

    Raises:
        smtplib.SMTPException: On any SMTP error.
    """
    # Create message
    msg = MIMEMultipart()
    msg["From"] = config["username"]
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    msg_string = msg.as_string()

    # All recipients for sendmail (To + CC)
    all_recipients = to_list + cc_list

    # Create secure SSL context
    context = ssl.create_default_context()

    server = None
    try:
        if config["smtp_use_tls"]:
            # Port 587 with STARTTLS
            logger.info(f"Connecting to {config['smtp_host']}:{config['smtp_port']} with STARTTLS")
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"], timeout=SMTP_TIMEOUT)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        else:
            # Port 465 with implicit SSL
            logger.info(f"Connecting to {config['smtp_host']}:{config['smtp_port']} with SSL")
            server = smtplib.SMTP_SSL(
                config["smtp_host"], config["smtp_port"], context=context, timeout=SMTP_TIMEOUT
            )

        server.login(config["username"], config["password"])
        server.sendmail(config["username"], all_recipients, msg_string)
        logger.info(f"Email sent successfully to {all_recipients}")

    finally:
        if server:
            try:
                server.quit()
            except smtplib.SMTPException:
                pass  # Ignore errors during cleanup

    # Save to Sent folder via IMAP if enabled
    if config.get("save_to_sent", True):
        try:
            save_to_sent_folder(config, msg_string)
        except Exception as e:
            # Log but don't fail the send operation
            logger.warning(f"Failed to save email to Sent folder: {e}")
