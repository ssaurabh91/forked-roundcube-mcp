"""MCP server for sending emails via Roundcube/SMTP."""

import asyncio
import json
import logging
import smtplib
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from app.email_service import (
    load_config,
    parse_email_list,
    send_email_smtp,
    validate_emails,
)

# Configure logging to stderr (stdout is used for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Create MCP server
app = Server("roundcube-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="send_email",
            description="Send an email via SMTP. Supports multiple recipients (comma-separated).",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address(es), comma-separated for multiple recipients",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain text email body",
                    },
                    "cc": {
                        "type": "string",
                        "description": "CC recipient(s), comma-separated for multiple (optional)",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "send_email":
        return await handle_send_email(arguments)

    raise ValueError(f"Unknown tool: {name}")


async def handle_send_email(arguments: dict) -> list[TextContent]:
    """Handle the send_email tool call."""
    try:
        # Load config
        config = load_config()

        # Parse recipients
        to_list = parse_email_list(arguments.get("to", ""))
        cc_list = parse_email_list(arguments.get("cc", "")) if arguments.get("cc") else []

        # Validate we have at least one recipient
        if not to_list:
            return [TextContent(type="text", text="Error: No valid recipients in 'to' field")]

        # Validate email addresses
        validate_emails(to_list)
        if cc_list:
            validate_emails(cc_list)

        # Get subject and body
        subject = arguments.get("subject", "")
        body = arguments.get("body", "")

        if not subject:
            return [TextContent(type="text", text="Error: Subject cannot be empty")]

        # Send email
        send_email_smtp(
            config=config,
            to_list=to_list,
            cc_list=cc_list,
            subject=subject,
            body=body,
        )

        # Success message
        result = f"Email sent successfully to {', '.join(to_list)}"
        if cc_list:
            result += f" (CC: {', '.join(cc_list)})"

        return [TextContent(type="text", text=result)]

    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Error: {e}")]
    except json.JSONDecodeError as e:
        return [TextContent(type="text", text=f"Error: Invalid JSON in config.json: {e}")]
    except KeyError as e:
        return [TextContent(type="text", text=f"Error: {e}")]
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: Invalid email address - {e}")]
    except smtplib.SMTPAuthenticationError:
        return [
            TextContent(
                type="text",
                text="Error: SMTP authentication failed. Check username/password in config.json",
            )
        ]
    except smtplib.SMTPConnectError as e:
        return [TextContent(type="text", text=f"Error: Could not connect to SMTP server: {e}")]
    except smtplib.SMTPException as e:
        return [TextContent(type="text", text=f"Error: SMTP error: {e}")]
    except Exception as e:
        logger.exception("Unexpected error sending email")
        return [TextContent(type="text", text=f"Error: Unexpected error: {e}")]


async def main() -> None:
    """Run the MCP server."""
    logger.info("Starting Roundcube MCP server")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
