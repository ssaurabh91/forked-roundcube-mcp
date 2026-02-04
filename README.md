# Roundcube MCP Server

<div align="center">

**MCP server for sending emails via Roundcube/SMTP through Claude Desktop**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io/)

[Quick Start](#-quick-start) • [Configuration](#-configuration) • [Claude Desktop Setup](#-claude-desktop-setup) • [Usage](#-usage)

</div>

---

## Overview

Roundcube MCP Server enables sending emails through your Roundcube webmail (or any SMTP server) using Claude Desktop. Simply ask Claude to send an email, and it handles the rest.

### Features

- **Send Emails**: Compose and send emails via natural language
- **Multiple Recipients**: Support for comma-separated To and CC recipients
- **Secure**: SSL and STARTTLS support for encrypted connections
- **Validation**: Email address validation before sending
- **Easy Setup**: Works with Claude Desktop out of the box

---

## Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **SMTP Account**: Roundcube webmail or any SMTP server credentials
- **Claude Desktop**: With MCP support

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/roundcube-mcp.git
cd roundcube-mcp

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install the package
pip install -e .

# Configure SMTP credentials
copy config.json.example config.json  # Windows
# cp config.json.example config.json  # macOS/Linux

# Edit config.json with your SMTP credentials
```

---

## Configuration

Edit `config.json` with your SMTP server details:

```json
{
    "smtp_host": "mail.example.com",
    "smtp_port": 465,
    "smtp_use_tls": false,
    "username": "user@example.com",
    "password": "your_password_here"
}
```

### Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| `smtp_host` | SMTP server hostname | `mail.example.com` |
| `smtp_port` | SMTP port number | `465` (SSL) or `587` (STARTTLS) |
| `smtp_use_tls` | Connection type | `false` for SSL (port 465), `true` for STARTTLS (port 587) |
| `username` | SMTP username (usually your email) | `user@example.com` |
| `password` | SMTP password | Your email password |

### Common SMTP Settings

| Provider | Host | Port | smtp_use_tls |
|----------|------|------|--------------|
| Roundcube (SSL) | Your mail server | 465 | `false` |
| Roundcube (STARTTLS) | Your mail server | 587 | `true` |
| Gmail | smtp.gmail.com | 587 | `true` |
| Outlook | smtp.office365.com | 587 | `true` |

---

## Claude Desktop Setup

Add the server to your Claude Desktop configuration.

### Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "roundcube-email": {
      "command": "python",
      "args": ["-m", "app.server"],
      "cwd": "c:\\Users\\YourUsername\\path\\to\\roundcube-mcp"
    }
  }
}
```

### macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "roundcube-email": {
      "command": "python",
      "args": ["-m", "app.server"],
      "cwd": "/Users/YourUsername/path/to/roundcube-mcp"
    }
  }
}
```

### Using Virtual Environment Python

For better isolation, point to the venv Python:

```json
{
  "mcpServers": {
    "roundcube-email": {
      "command": "c:\\path\\to\\roundcube-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "app.server"],
      "cwd": "c:\\path\\to\\roundcube-mcp"
    }
  }
}
```

**After editing, restart Claude Desktop.**

---

## Usage

Once configured, ask Claude to send emails using natural language:

```
"Send an email to john@example.com with subject 'Meeting Tomorrow'
and body 'Hi John, Let's meet at 2pm tomorrow. Best regards.'"

"Email alice@example.com and bob@example.com about the project update.
Subject: Project Status, Body: The project is on track for delivery."

"Send a message to team@example.com with CC to manager@example.com
Subject: Weekly Report, Body: Here's our weekly progress report."
```

### Available Tool

| Tool | Parameters | Description |
|------|------------|-------------|
| `send_email` | `to` (required), `subject` (required), `body` (required), `cc` (optional) | Send an email via SMTP |

---

## Testing

### Test SMTP Connection Directly

Create a test script to verify your SMTP settings work:

```python
# test_smtp.py
from app.email_service import load_config, send_email_smtp

config = load_config()
send_email_smtp(
    config=config,
    to_list=["your.test.email@example.com"],
    cc_list=[],
    subject="Test from roundcube-mcp",
    body="This is a test email to verify SMTP configuration."
)
print("Email sent successfully!")
```

Run:
```bash
python test_smtp.py
```

---

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `config.json not found` | Missing configuration | Copy `config.json.example` to `config.json` and edit |
| `SMTP authentication failed` | Wrong credentials | Check username/password in `config.json` |
| `Could not connect to SMTP server` | Wrong host/port or firewall | Verify SMTP settings, check firewall |
| `Invalid email address` | Malformed email | Check email format (e.g., `user@domain.com`) |

### Debug Mode

To see detailed logs, check stderr output when running the server manually:

```bash
python -m app.server
```

---

## Project Structure

```
roundcube-mcp/
├── app/
│   ├── __init__.py          # Package marker
│   ├── server.py            # MCP server implementation
│   └── email_service.py     # SMTP logic and validation
├── config.json.example      # Configuration template
├── config.json              # Your configuration (git-ignored)
├── pyproject.toml           # Project dependencies
├── README.md                # This file
└── LICENSE                  # MIT License
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) - LLM-tool integration standard
- [Anthropic](https://www.anthropic.com/) - Claude and MCP SDK
