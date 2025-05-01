# Weekly-Updater

Weekly-Updater is a tool that automates the generation of weekly reports by fetching GitHub pull request (PR) details, summarizing them using OpenAI, and sending these summaries directly to users on Slack. This project streamlines the reporting process for teams, offering efficient and automated PR tracking with insightful summaries.

By default, the prompt groups a developer’s PRs into three categories: “New Features Added,” “Incremental Improvements,” and “Bugs Fixed.” However, this structure can be easily customized by modifying the prompt to fit specific team needs. Here's an example of how this reported for a developer at Defog AI (YC W23):

<img width="973" alt="Screenshot 2025-05-01 at 2 55 19 PM" src="https://github.com/user-attachments/assets/dc734aaa-3ca9-404d-95dd-4e4bcbaaf245" />

## Features

#### Automated PR Fetching: Pulls data from GitHub repositories for the entire organization, grouped by users.

#### Summarization with OpenAI: Automatically generates summaries of PRs using GPT-based models for concise updates.

#### Slack Integration: Sends the generated summaries to the respective users on Slack, with the option to confirm or manually edit the summary.

#### Interactive Slack UI: Users can confirm the summary or make edits via a Slack modal, ensuring accurate and well-tailored reports. Upon clicking the "Confirm" button, the summary is sent to general channel on Slack. The app on defog slack that is connected to this is called `Weekly Updater`.

#### Modularized Design: Built with a clean, modular structure for easy maintenance and scalability.

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Set Environment Variables

Create a copy of the `.env.template` file and rename it to `.env`. Fill in the required environment variables.

### Run the FastAPI server

```bash
python3 main.py
```

The local host will need to be made available remotely using a service like [`ngrok`](https://ngrok.com/) to allow Slack to send requests to the local server. Then, update the `slack/events` and `slack/interactions` URLs on the [`Slack App`](https://api.slack.com/apps) under the `Event Subscriptions` and `Interactivity & Shortcuts` sections, respectively. This is required when testing via localhost. Once the app is deployed, the URLs of the deployed backend server will need to be updated in the Slack app.

### Run the main script

```bash
python3 main.py
```

This script fetches PRs from GitHub, generates summaries using OpenAI, and sends them to the respective users on Slack. It is advised to run a cron job to run this script weekly or whatever interval you want for updates.
