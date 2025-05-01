"""Module to fetch data about PRs from GitHub API from the last Monday to the current date."""

import requests
import logging
from typing import List, Dict, Any
from datetime import datetime
from .utils import get_last_monday
from .config import HEADERS, ORG_NAME


def active_repo(repo: Dict) -> bool:
    """Check if a repository is active based on its updated_at"""
    return datetime.strptime(repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ") >= get_last_monday()


def fetch_repos():
    """
    Fetch all repositories in the organization.

    Returns:
        List[Dict[str, Any]]: A list of repositories in dictionary form. If the request
        fails, it returns an empty list.
        The dictionary contains the following:
        keys: id, node_id, name, full_name, private, html_url, description, fork etc
    """
    url = f"https://api.github.com/orgs/{ORG_NAME}/repos"
    params = {"per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        logging.error(f"Failed to fetch repositories: {response.status_code}")
        return []
    repo_data = response.json()
    active_repos = [repo for repo in repo_data if active_repo(repo)]
    for repo in active_repos:
        logging.info(f"Active repo: {repo['name']}")
    return active_repos


def fetch_prs_for_repo(repo_name: str) -> List[Dict[str, Any]]:
    """
    Fetch all pull requests (PRs) for a given repository.

    This function sends a GET request to the GitHub API to fetch all pull requests
    (both open and closed) for the specified repository. It returns a list of dictionaries,
    where each dictionary contains details of a pull request.

    Args:
        repo_name (str): The name of the repository for which to fetch pull requests.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries representing pull requests. If the request
        fails, it returns an empty list.
    """
    pr_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/pulls"
    response = requests.get(pr_url, headers=HEADERS, params={"state": "all"})

    if response.status_code != 200:
        logging.error(f"Failed to fetch PRs for {repo_name}: {response.status_code}")
        return []

    return response.json()


def filter_prs_since_monday(prs):
    """Filter pull requests created since the last Monday."""
    last_monday = get_last_monday()
    filtered_prs = [
        pr
        for pr in prs
        if datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ") >= last_monday
    ]
    return filtered_prs


def get_pr_details(pr_data):
    """Fetch the commit messages and overall stats for a PR.
    Input:
        pr_data: A dictionary containing the PR data (repo name and PR details).
    Output:
        A dictionary containing the PR details (title, state, description, URL, changes, commit).

    """
    pr = pr_data["pr"]
    repo_name = pr_data["repo"]
    pr_number = pr["number"]

    pr_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/pulls/{pr_number}"
    pr_response = requests.get(pr_url, headers=HEADERS)

    if pr_response.status_code != 200:
        logging.error(
            f"Failed to fetch details for PR #{pr_number}: {pr_response.status_code}"
        )
        return {}

    pr_info = pr_response.json()
    commits_url = pr_info["commits_url"]
    commits_response = requests.get(commits_url, headers=HEADERS)

    if commits_response.status_code != 200:
        logging.error(
            f"Failed to fetch commits for PR #{pr_number}: {commits_response.status_code}"
        )
        return {}

    commits = commits_response.json()
    commit_messages = [commit["commit"]["message"] for commit in commits]

    return {
        "title": pr_info["title"],
        "number": pr_info["number"],
        "state": pr_info["state"],
        "description": pr_info["body"] or "No description provided.",
        "url": pr_info["html_url"],
        "changes": pr_info.get("additions", 0) + pr_info.get("deletions", 0),
        "commit_messages": commit_messages,
    }
