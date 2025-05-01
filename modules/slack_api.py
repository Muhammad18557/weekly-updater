"""
Functions for Slack API interactions from sending a message to a user, handling modal submissions, 
updating messages, opening modals for editing, and posting to the general channel.
"""

from fastapi import HTTPException
from slack_sdk.errors import SlackApiError
import logging
import json
from .config import GENERAL_CHANNEL, slack_client

# Initialize logging
logging.basicConfig(filename="weekly_report.log", level=logging.INFO)


async def send_message_to_user(user_id: str, message: str):
    """
    Send a message with action buttons to a Slack user.

    Args:
        user_id (str): The Slack user ID.
        message (str): The message to send to the user.

    Returns:
        dict: A response dictionary indicating the message status.
    """
    try:
        response = await slack_client.chat_postMessage(
            channel=user_id,
            text=message,
            mrkdwn=True,
            attachments=[
                {
                    "text": "Do you confirm this summary to be posted to the general channel? You can also edit it manually.",
                    "fallback": "You are unable to confirm.",
                    "callback_id": "confirm_summary",
                    "color": "#3AA3E3",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "confirm",
                            "text": "Confirm",
                            "type": "button",
                            "value": "confirm",
                        },
                        {
                            "name": "manual_edit",
                            "text": "Edit",
                            "type": "button",
                            "value": "manual_edit",
                            "action_id": "edit",
                        },
                    ],
                }
            ],
        )
        return {
            "message": "Message sent successfully.",
            "ts": response["ts"],
            "channel": user_id,
        }
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return {"error": str(e)}


async def handle_modal_submission(payload):
    """Handle the modal submission to update the original message."""
    try:
        # Extract the new message from the modal input
        new_message = payload["view"]["state"]["values"]["edit_block"]["message_input"][
            "value"
        ]

        # Retrieve metadata to identify the message to update
        metadata = json.loads(payload["view"].get("private_metadata", "{}"))
        channel_id = metadata.get("channel_id")
        message_ts = metadata.get("message_ts")

        if not channel_id or not message_ts:
            raise ValueError("Missing channel_id or message_ts in metadata.")

        # Update the original message
        await update_message(channel_id, message_ts, new_message)
    except Exception as e:
        print(f"Error processing modal submission: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process modal submission."
        )


async def update_message(channel, ts, new_text):
    """Update the original Slack message with the new content and keep the buttons."""
    try:
        # Include the same attachments (buttons) that were part of the original message
        response = await slack_client.chat_update(
            channel=channel,
            ts=ts,
            text=new_text,
            mrkdwn=True,
            attachments=[
                {
                    "text": "Do you confirm this summary to be posted to the general channel? You can also edit it manually.",
                    "fallback": "You are unable to confirm.",
                    "callback_id": "confirm_summary",
                    "color": "#3AA3E3",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "confirm",
                            "text": "Confirm",
                            "type": "button",
                            "value": "confirm",
                        },
                        {
                            "name": "manual_edit",
                            "text": "Edit",
                            "type": "button",
                            "value": "manual_edit",
                            "action_id": "edit",
                        },
                    ],
                }
            ],  # Include the attachments to retain buttons
        )
        print(f"Message updated: {response}")
    except SlackApiError as e:
        print(f"Error updating message: {e.response['error']}")


async def open_edit_modal(trigger_id, message_text, ts, channel_id):
    """Open a Slack modal for manual editing."""
    try:
        print(f"Trigger ID: {trigger_id}, Channel ID: {channel_id}, TS: {ts}")

        # Open the modal
        response = await slack_client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "edit_modal",
                "title": {"type": "plain_text", "text": "Edit Message"},
                "private_metadata": json.dumps(
                    {"channel_id": channel_id, "message_ts": ts}
                ),  # Include metadata
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "edit_block",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "message_input",
                            "initial_value": message_text,  # Prepopulate with the message text
                            "multiline": True,  # Ensure multi-line input
                        },
                        "label": {"type": "plain_text", "text": "Edit the message"},
                    }
                ],
                "submit": {"type": "plain_text", "text": "Submit"},
            },
        )
        print(f"Modal opened successfully: {response}")

    except SlackApiError as e:
        print(f"Error opening modal: {e.response['error']}")


async def post_to_general_channel(summary_message: str):
    """Post the confirmed summary to the general channel."""
    try:
        response = await slack_client.chat_postMessage(
            channel=GENERAL_CHANNEL,
            text=f"{summary_message}",
            mrkdwn=True,
        )
        print(f"Summary posted to the general channel: {response}")
    except SlackApiError as e:
        print(f"Error posting to general channel: {e.response['error']}")
        raise HTTPException(status_code=500, detail="Failed to post summary.")
