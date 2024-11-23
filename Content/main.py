import os
from dotenv import load_dotenv
from typing import List
from github_api import (
    search_repos,
    get_repo_commits,
    parse_repo_contents,
    print_content_tree
)


def main_menu():
    print("\nGitHub Utility Tool")
    print("--------------------")
    print("1. Search for repositories")
    print("2. View repository information")
    print("3. View repository commits")
    print("4. Parse and view repository contents")
    print("5. Exit")
    return input("Choose an option (1-5): ")


def display_repos(repos: List[dict]):
    for idx, repo in enumerate(repos, start=1):
        print(f"[{idx}] {repo['full_name']}")


def display_commits(commits: List[dict]):
    for idx, commit in enumerate(commits, start=1):
        print(f"[{idx}] {commit['commit']['message']}")


def handle_search_repos(api_version: str, token: str):
    keywords = input("Enter search keywords (space-separated): ").split()
    repos = search_repos(keywords, api_version, token)

    if not repos:
        print("\nNo repositories found.")
        return

    display_repos(repos)

    while True:
        selection = input(
            "\nEnter the number of a repository to display its details (or press Enter to return to the main menu): ")

        if not selection:
            break

        try:
            repo_idx = int(selection) - 1
            if 0 <= repo_idx < len(repos):
                repo = repos[repo_idx]
                print(f"\nRepository: {repo['full_name']}")
                print(f"Description: {repo.get('description', 'No description')}")
                print(f"Stars: {repo['stargazers_count']}, Forks: {repo['forks_count']}")
                print(f"URL: {repo['html_url']}")
            else:
                print("Invalid selection. Please choose a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def handle_repo_commits(api_version: str, token: str):
    owner = input("Enter repository owner: ")
    repo = input("Enter repository name: ")
    starting_page = int(input("Enter starting page number: "))
    commits = get_repo_commits(owner, repo, api_version, token, starting_page)

    if not commits:
        print("\nNo commits found.")
        return

    display_commits(commits)

    while True:
        selection = input(
            "\nEnter the number of a commit to display its details (or press Enter to return to the main menu): ")

        if not selection:
            break

        try:
            commit_idx = int(selection) - 1
            if 0 <= commit_idx < len(commits):
                commit = commits[commit_idx]
                print(f"\nCommit Message: {commit['commit']['message']}")
                print(f"Author: {commit['commit']['author']['name']}")
                print(f"Date: {commit['commit']['author']['date']}")
                print(f"URL: {commit['html_url']}")
            else:
                print("Invalid selection. Please choose a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def handle_repo_contents(api_version: str, token: str):
    owner = input("Enter repository owner: ")
    repo = input("Enter repository name: ")

    print("\nParsing repository contents...")
    root_objects = parse_repo_contents(owner, repo, api_version, token)
    print_content_tree(root_objects)

    while True:
        path = input("\nEnter the path of a content to inspect (or press Enter to return to the main menu): ")
        if not path:
            break

        # Search for the content in the tree
        def find_content(objects, _path_parts):
            for obj in objects:
                if obj.name == _path_parts[0]:
                    if len(_path_parts) == 1:
                        return obj
                    return find_content(obj.children, _path_parts[1:])
            return None

        path_parts = path.split("/")
        content = find_content(root_objects, path_parts)

        if content:
            print(f"\nName: {content.name}")
            print(f"Type: {content.type}")
            print(f"Parent: {content.parent.name if content.parent else 'None'}")
        else:
            print("Content not found. Please check the path and try again.")


if __name__ == "__main__":
    load_dotenv()

    DEFAULT_API_VERSION = "2022-11-28"

    github_token = os.environ.get("GITHUB_TOKEN")
    github_api_version = os.environ.get("GITHUB_API_VERSION", DEFAULT_API_VERSION)

    if not github_token:
        print("Could not find a GitHub token!\n"
              "Make sure you have GITHUB_TOKEN set up in your environment!")
        exit(1)

    while True:
        choice = main_menu()
        if choice == "1":
            handle_search_repos(github_api_version, github_token)
        elif choice == "2":
            handle_repo_commits(github_api_version, github_token)
        elif choice == "3":
            handle_repo_contents(github_api_version, github_token)
        elif choice == "5":
            print("Exiting the application. Goodbye!")
            break
        else:
            print("Invalid choice. Please select an option from 1 to 5.")
