"""FastAPI server for handling Slack events and interactions."""

from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from slack_sdk.web.async_client import AsyncWebClient
import json

from modules.config import SLACK_TOKEN
from modules.slack_api import (
    post_to_general_channel,
    handle_modal_submission,
    open_edit_modal,
)

# Initialize FastAPI app and Slack client
app = FastAPI()
slack_client = AsyncWebClient(token=SLACK_TOKEN)  # Use AsyncWebClient
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({"status": "I am a healthy Server!"})


@router.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack event subscriptions."""
    print("Received an event from Slack.")
    data = await request.json()

    # Handle Slack's URL verification challenge
    if "challenge" in data:
        print("Responding to Slack URL verification.")
        return {"challenge": data["challenge"]}

    # print(f"Event data: {json.dumps(data, indent=2)}")
    return JSONResponse({"status": "ok"})


@router.post("/slack/interactions")
async def handle_interactions(request: Request):
    """Handle interactive elements like button clicks and modal submissions from Slack."""
    print("Received interaction request.")
    try:
        # Extract and print form data
        form_data = await request.form()
        payload = json.loads(form_data["payload"])
        print(f"Received interaction payload: {json.dumps(payload, indent=2)}")

        # Check if the interaction is a modal submission
        if payload["type"] == "view_submission":
            await handle_modal_submission(payload)
            return JSONResponse(
                {"response_action": "clear"}
            )  # Clear the modal after submission

        # Handle button clicks (like "Edit Manually")
        callback_id = payload.get("callback_id")
        action_value = payload["actions"][0]["value"]

        if callback_id == "confirm_summary":
            if action_value == "confirm":
                # Pass the original message (or summary) to be posted
                original_message = payload["original_message"]["text"]
                await post_to_general_channel(original_message)
                return JSONResponse({"text": "Summary confirmed and posted."})
            elif action_value == "llm_edit":
                print("Requesting LLM to revise the summary...")
                return JSONResponse({"text": "Requesting LLM to revise the summary..."})
            elif action_value == "manual_edit":
                # Extract the needed information
                trigger_id = payload["trigger_id"]
                original_message = payload["original_message"]["text"]
                message_ts = payload[
                    "message_ts"
                ]  # Extract timestamp of the original message
                channel_id = payload["channel"]["id"]  # Extract channel ID

                # Pass the required parameters to the modal opening function
                await open_edit_modal(
                    trigger_id, original_message, message_ts, channel_id
                )
                return JSONResponse(
                    status_code=200,
                    content="Please press confirm even if no edits were made to get back the original message.",
                )

        return JSONResponse({"text": "Unknown action."})

    except Exception as e:
        print(f"Error processing interaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to process interaction.")


# Mount the router
app.include_router(router)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=80, reload=True)
