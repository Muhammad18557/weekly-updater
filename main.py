""" Main script and the entry point to fetch PRs, generate reports, and send summaries via Slack. """

import logging
import asyncio
from modules.config import USER_MAPPING
from modules.github_api import fetch_repos, fetch_prs_for_repo, filter_prs_since_monday
from modules.summary import compile_report_for_user, summarise_report_using_openai
from modules.slack_api import send_message_to_user

# Initialize logging
logging.basicConfig(filename="weekly_report.log", level=logging.INFO)


async def fetch_prs_for_all_repos() -> dict:
    """
    Fetch all PRs across all repositories in the organization and group them by user.

    This function uses the `fetch_repos` and `fetch_prs_for_repo` functions to retrieve repositories and
    their associated PRs. PRs are filtered to include only those created since the last Monday.

    Returns:
        dict: A dictionary where keys are github usernames and values are lists of PRs created since the last Monday.
    """
    print("Fetching PRs for all repositories...")
    # Fetch repositories in the organization
    repos = fetch_repos()
    if not repos:
        logging.error("Failed to fetch repositories. Exiting...")
        return {}
    user_pr_map = {}

    for repo in repos:
        repo_name = repo["name"]
        prs = fetch_prs_for_repo(repo_name)

        # Filter PRs created since last Monday
        filtered_prs = filter_prs_since_monday(prs)

        # Group PRs by user
        for pr in filtered_prs:
            author = pr["user"]["login"]
            if author not in user_pr_map:
                user_pr_map[author] = []
            user_pr_map[author].append({"repo": repo_name, "pr": pr})
    logging.info(f"PRs fetched for {len(user_pr_map)} users.")
    for user, prs in user_pr_map.items():
        logging.info(f"User: {user}, PRs: {len(prs)}")
    return user_pr_map


async def process_reports(user_pr_map: dict):
    """
    Process reports for all users, generate a report, and send a summary via Slack.

    Args:
        user_pr_map (dict): A dictionary mapping GitHub usernames to their associated PRs.
    """
    print("Processing and sending messages...")
    for github_username, prs in user_pr_map.items():
        # Fetch Slack ID for the user
        slack_id = USER_MAPPING.get(github_username)
        if not slack_id:
            logging.warning(f"No Slack ID found for GitHub user: {github_username}")
            continue

        # Generate the report for the user
        logging.info(f"Generating report for {github_username}...")
        report = compile_report_for_user(github_username, prs)

        # Generate a summary of the report using the LLM
        summary = summarise_report_using_openai(report, github_username)

        # Send the summary to the user via Slack
        await send_message_to_user(slack_id, summary)


if __name__ == "__main__":
    # Entry point for the script
    logging.info("Fetching PRs for all repositories...")
    user_pr_map = asyncio.run(fetch_prs_for_all_repos())

    # Process and send reports asynchronously
    asyncio.run(process_reports(user_pr_map))
