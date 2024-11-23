import datetime
import time
import traceback
from typing import List, Union

import requests

# Base URL for the GitHub API
GITHUB_BASE_URL = "https://api.github.com"

# Delay between pagination requests to avoid hitting rate limits
PAGINATION_DELAY_SECONDS = 1


class GHContentObject:
    """
    Represents a content object in a GitHub repository, which can be a file or a directory.

    Attributes:
        type (str): The type of the object ('file' or 'dir').
        name (str): The name of the content object.
        parent (GHContentObject): The parent directory of the object.
        children (List[GHContentObject]): List of child objects if the object is a directory.
    """
    def __init__(self, data: dict, parent: 'GHContentObject' = None, children: List['GHContentObject'] = None):
        self.type = data['type']
        self.name = data['name']
        self.parent = parent
        self.children = children if children is not None else []

    def add_child(self, child: 'GHContentObject'):
        """
        Adds a single child object to the current object.
        """
        self.children.append(child)

    def add_children(self, children: List['GHContentObject']):
        """
        Adds multiple child objects to the current object.
        """
        self.children.extend(children)


def print_content_tree(root_objects: List[GHContentObject]):
    """
    Prints a visual representation of the content tree starting from the root objects.

    Args:
        root_objects (List[GHContentObject]): List of root-level content objects.
    """
    print()

    def _print_tree(node: GHContentObject, prefix: str = "", is_last: bool = True):
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{node.name}")

        if node.type == "dir" and node.children:
            new_prefix = prefix + ("    " if is_last else "│   ")
            for _i, _child in enumerate(node.children):
                _print_tree(_child, new_prefix, is_last=(_i == len(node.children) - 1))

    for i, root in enumerate(root_objects):
        print(root.name)
        for j, child in enumerate(root.children):
            _print_tree(child, "", is_last=(j == len(root.children) - 1))


def pause_until_utc(until: int):
    """
    Pauses execution until a specified UTC timestamp.

    Args:
        until (int): The UTC timestamp to wait until.
    """
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)
        if now.timestamp() >= until:
            print()
            return
        else:
            remaining = datetime.datetime.fromtimestamp(until, datetime.timezone.utc) - now
            remaining_seconds = int(remaining.total_seconds())
            days, remainder = divmod(remaining_seconds, 86400)  # 86400 seconds in a day
            hours, remainder = divmod(remainder, 3600)  # 3600 seconds in an hour
            minutes, seconds = divmod(remainder, 60)

            print("\rWaiting for the rate limit to reset. Time remaining: "
                  f"{days} day(s) {hours} hour(s) {minutes} minute(s) {seconds} second(s)",
                  end=''
                  )
        time.sleep(0.5)


def get_repo_folder(owner: str, repo: str, api_version: str, access_token: str,
                    path: str = "") -> List[GHContentObject]:
    """
    Retrieves the contents of a specific folder in a GitHub repository.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        api_version (str): The API version to use.
        access_token (str): The personal access token for authentication.
        path (str): The folder path within the repository.

    Returns:
        List[GHContentObject]: List of content objects in the folder.
    """
    url = f"{GITHUB_BASE_URL}/repos/{owner}/{repo}/contents/{path}"
    params = {
        "per_page": 100,
        "page": 1
    }
    headers = {
        "X-GitHub-Api-Version": api_version,
        "Authorization": f"Bearer {access_token}"
    }

    results = []

    while True:
        print(f"\rParsing page {params['page']} of folder {path}", end='')
        try:
            response = requests.get(url, headers=headers, params=params)

            if not response.ok:
                if response.status_code in [403, 429] and int(response.headers['x-ratelimit-remaining']) <= 0:
                    print()
                    pause_until_utc(int(response.headers['x-ratelimit-reset']))
                elif response.status_code == 403:
                    print(f"\nThe repository {owner}/{repo} appears to be private")
                    return []
                elif response.status_code == 404:
                    print(f"\nCould not find {owner}/{repo} repository")
                    return []
                else:
                    print()
                    print(f"\nParsing error: {response.text}")
                    return []
            else:
                data = response.json()
                if len(data) <= 0:
                    break
                else:
                    results.extend([GHContentObject(x) for x in data])
        except Exception as e:
            print()
            print(f"An unhandled exception occurred: {e}")
            print(traceback.format_exc())
        return results


def parse_repo_contents(owner: str, repo: str, api_version: str, access_token: str,
                        path: str = "", parent_object: GHContentObject = None) -> List[GHContentObject]:
    """
    Recursively parses the contents of a GitHub repository, including nested directories.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        api_version (str): The API version to use.
        access_token (str): The personal access token for authentication.
        path (str): The folder path to start parsing from.
        parent_object (GHContentObject): The parent object for nested structures.

    Returns:
        List[GHContentObject]: List of all parsed content objects.
    """
    results = []

    folder_contents = get_repo_folder(owner, repo, api_version, access_token, path)

    if parent_object is None:
        results.extend(folder_contents)
    else:
        parent_object.add_children(folder_contents)

    for content in folder_contents:
        if content.type == "dir":
            parse_repo_contents(owner, repo, api_version, access_token, f"{path}/{content.name}", content)

    return results


def get_repo_info(owner: str, repo: str, api_version: str, access_token: str) -> Union[dict, None]:
    """
    Retrieves metadata about a specific GitHub repository.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        api_version (str): The API version to use.
        access_token (str): The personal access token for authentication.

    Returns:
        Union[dict, None]: A dictionary containing repository metadata, or None if the repository is inaccessible.
    """
    url = f"{GITHUB_BASE_URL}/repos/{owner}/{repo}"
    headers = {
        "X-GitHub-Api-Version": api_version,
        "Authorization": f"Bearer {access_token}"
    }

    print(f"Trying to get repo {owner}/{repo}...")

    try:
        response = requests.get(url, headers=headers)

        if not response.ok:
            if response.status_code in [403, 429] and int(response.headers['x-ratelimit-remaining']) <= 0:
                pause_until_utc(int(response.headers['x-ratelimit-reset']))
            elif response.status_code == 403:
                print(f"The repository {owner}/{repo} appears to be private")
                return None
            elif response.status_code == 404:
                print(f"Could not find {owner}/{repo} repository")
                return None
            else:
                print()
                print(f"Parsing error: {response.text}")
                return None
        else:
            return response.json()
    except Exception as e:
        print()
        print(f"An unhandled exception occurred: {e}")
        print(traceback.format_exc())


def get_repo_commits(owner: str, repo: str, api_version: str, access_token: str, starting_page: int) -> List[dict]:
    """
    Retrieves a list of commits from a GitHub repository.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        api_version (str): The API version to use.
        access_token (str): The personal access token for authentication.
        starting_page (int): The page number to start retrieving commits from.

    Returns:
        List[dict]: A list of commit objects containing metadata about each commit.
    """
    url = f"{GITHUB_BASE_URL}/repos/{owner}/{repo}/commits"
    params = {
        "per_page": 100,
        "page": starting_page
    }
    headers = {
        "X-GitHub-Api-Version": api_version,
        "Authorization": f"Bearer {access_token}"
    }

    print(f"Trying to get commits of repo {owner}/{repo}...")

    results = []

    while True:
        print(f"\rParsing page {params['page']}", end='')
        try:
            response = requests.get(url, headers=headers, params=params)

            if not response.ok:
                if response.status_code in [403, 429] and int(response.headers['x-ratelimit-remaining']) <= 0:
                    print()
                    pause_until_utc(int(response.headers['x-ratelimit-reset']))
                elif response.status_code == 403:
                    print(f"\nThe repository {owner}/{repo} appears to be private")
                    return []
                elif response.status_code == 404:
                    print(f"\nCould not find {owner}/{repo} repository")
                    return []
                else:
                    print()
                    print(f"\nParsing error: {response.text}")
                    return []
            else:
                data = response.json()
                if len(data) <= 0:
                    break
                else:
                    results += data
        except Exception as e:
            print()
            print(f"An unhandled exception occurred: {e}")
            print(traceback.format_exc())
        return results


def search_repos(keywords: List[str], api_version: str, access_token: str, starting_page: int = 1) -> List[dict]:
    """
    Searches for GitHub repositories based on a list of keywords.

    Args:
        keywords (List[str]): A list of keywords to search for.
        api_version (str): The API version to use.
        access_token (str): The personal access token for authentication.
        starting_page (int): The page number to start the search from.

    Returns:
        List[dict]: A list of repository objects matching the search criteria.
    """
    url = f"{GITHUB_BASE_URL}/search/repositories"
    params = {
        "q": '+'.join(keywords),
        "per_page": 100,
        "page": starting_page
    }
    headers = {
        "X-GitHub-Api-Version": api_version,
        "Authorization": f"Bearer {access_token}"
    }
    results = []

    print(f"Starting search for keywords {', '.join(keywords)}")

    while params['page'] <= 10:  # Limit to the first 10 pages of results
        print(f"\rParsing page {params['page']}/10...", end='')
        try:
            response = requests.get(url, params=params, headers=headers)

            if not response.ok:
                if response.status_code in [403, 429] and int(response.headers['x-ratelimit-remaining']) <= 0:
                    print()
                    pause_until_utc(int(response.headers['x-ratelimit-reset']))
                elif response.status_code == 422:  # Invalid search query
                    break
                else:
                    print()
                    print(f"Parsing error: {response.text}")
                    break
            elif len(response.json()['items']) <= 0:
                break
            results += response.json()['items']
            params['page'] += 1
        except Exception as e:
            print()
            print(f"An unhandled exception occurred: {e}")
            print(traceback.format_exc())
        time.sleep(PAGINATION_DELAY_SECONDS)
    print()

    return results

