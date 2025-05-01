"""This module reads the configuration and env file for constants, initialises a Slack client the and GitHub header for authetication."""

import os
import json
from slack_sdk.web.async_client import AsyncWebClient
from dotenv import load_dotenv


load_dotenv()


def load_config():
    with open("config.json") as f:
        return json.load(f)


config = load_config()

# Access tokens and settings
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ORG_NAME = config["organization_name"]
GENERAL_CHANNEL = config["general_channel"]
USER_MAPPING = config["github_to_slack_user_mapping"]


# Initialize Slack client
slack_client = AsyncWebClient(token=SLACK_TOKEN)


# HEADERS for GitHub API
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
