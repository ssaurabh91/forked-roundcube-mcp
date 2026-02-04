"""List all IMAP folders to find the correct Sent folder name."""

import imaplib
import os

# Use environment variables or hardcode for testing
IMAP_HOST = os.environ.get("IMAP_HOST", "mail.encureit.com")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
USERNAME = os.environ.get("SMTP_USERNAME", "saurabh.sachdev@encureit.com")
PASSWORD = os.environ.get("SMTP_PASSWORD", "")

if not PASSWORD:
    PASSWORD = input("Enter your email password: ")

print(f"Connecting to {IMAP_HOST}:{IMAP_PORT}...")
imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
imap.login(USERNAME, PASSWORD)

print("\n=== Your IMAP Folders ===\n")
status, folders = imap.list()
for folder in folders:
    # Decode folder info
    folder_str = folder.decode("utf-8")
    print(folder_str)

imap.logout()
print("\n=== Done ===")
print("\nLook for the Sent folder name above (e.g., 'Sent', 'INBOX.Sent', 'Sent Items', etc.)")
