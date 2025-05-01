"""
Functions to compile a detailed report for a specific user summarizing their PRs and commits, 
and to generate a concise summary of the user's weekly PR work using an LLM.
"""

import logging
import openai
import re
from modules.config import OPENAI_API_KEY
from modules.utils import get_last_monday
from modules.github_api import get_pr_details

openai.api_key = OPENAI_API_KEY


def compile_report_for_user(username: str, user_prs: list) -> str:
    """
    Compile a detailed report for a specific user summarizing their PRs and commits.

    Args:
        username (str): The GitHub username of the user.
        user_prs (list): List of pull request data for the user.

    Returns:
        str: A formatted string report for the user's weekly pull request activity.
    """
    report = f"Weekly Update for {username} (from {get_last_monday().strftime('%Y-%m-%d')} to today):\n\n"

    for pr_data in user_prs:
        details = get_pr_details(pr_data)
        report += (
            f"Repository: {pr_data['repo']}\n"
            f"PR #{details['number']}: {details['title']} ({details['state']})\n"
            f"Description: {details['description']}\n"
            f"URL: {details['url']}\n"
            f"Changes: {details['changes']} lines\n"
            f"Commits:\n"
        )
        for message in details["commit_messages"]:
            report += f"- {message}\n"
        report += "\n" + "-" * 50 + "\n"

    return report.strip()


def summarise_report_using_openai(report: str, username: str) -> str:
    """
    Generate a concise summary of the user's weekly PR work using an LLM.

    Args:
        report (str): The detailed PR report.
        username (str): The GitHub username of the user.

    Returns:
        str: A summarized version of the PR report, suitable for posting in Slack.
    """
    # mapping of GitHub usernames to actual names
    user_name_actual_name = {
        "Muhammad18557": "Abdullah",
        "rishsriv": "Rishabh",
        "man-shar": "Manas",
        "wongjingping": "Jing Ping",
        "thedivtagguy": "Aman",
    }
    username = user_name_actual_name.get(username, username)
    print(f"Summarizing {username}'s weekly work...")
    messages = [
        {
            "role": "system",
            "content": f"""
You are responsible for writing updates for software engineers at defog-ai summarizing their weekly work. The person's name is {username}. Focus on the work done, keeping it simple and write in first person as if the person is writing himself.
Must include the person's name in the first line emboldened. Summarize the key work done in the PR's in the following sections:
- New Features Added
- Incremental Improvements
- Bugs Fixed

Instructions:
- If any of the sections is not applicable, skip it.
- For each section, provide a brief summary of the work done in that area and list the relevant PR(s) with a concise description as a sub-point.
- Include the relevant technical details (e.g. name of component that had a bug) in the summary but keep it concise.
- If the purpose / motivation for the PR is provided, include that in the summary as well.
- If multiple PR's are related (e.g. building out a new feature, or fixing the same bug), group them together under the same section.
- Add the PR's URL as slack message links at the end of the sub-point, formatted as per slack's API message format e.g. <https://github.com/defog-ai/defog-ai/pull/1|Link 1>. Number the links starting from 1 and reset for each new bullet.

Eg output format:
Weekly update for {username}:
**New Features Added**:
    - (Feature 1's description). PR: [<https://github.com/defog-ai/defog-ai/pull/1|Link 1>, ...]
    ...
**Incremental Improvements**:
    - (Improvement 1's description). PR: [<https://github.com/defog-ai/defog-ai/pull/2|Link 1>, ...]
    ...
**Bugs Fixed**:
    - (Bug 1's description). PR: [<https://github.com/defog-ai/defog-ai/pull/3|Link 1>, ...]
    ...
            """,
        },
        {
            "role": "user",
            "content": f"""
Here are the details of the PRs opened this week: {report}. Start with "Weekly update for {username}:\n" and then add the relevant sections below.
            """,
        },
    ]

    # Call OpenAI GPT-4 model to summarize the report
    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_completion_tokens=1000,
        temperature=0,
    )
    summary = completion.choices[0].message.content
    summary = re.sub(r"\*\*", "*", summary)
    print(f"Summary of {username}'s weekly work:\n{summary}")
    logging.info(f"Summary of the user's weekly work:\n{summary}")
    return summary
