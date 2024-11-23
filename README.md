# Data Source API Analyst Challenge
This repository contains results of researching and testing [GitHub API](https://docs.github.com/en/rest/quickstart?apiVersion=2022-11-28)
and a primitive tool made as a Python script extracting data from API based of the Client Needs in the assignment

# What is used
For testing and researching the API `Postman` and `GitHub docs` were used

The python tool uses `requests` to retrieve data from API and `python-dotenv` library to allow setting authentication token
and API version in the .env file

# How to use the tool
The Python tool was made and tested using `Python 3.12`, but other v3 versions should work fine as well

In order to use the tool you will have to:
1. Install Python v3 with pip if you do not have it already
2. Download and extract the Content folder of the repo anywhere on your PC/server
3. Open cmd/linux shell in the resulting folder
4. Run `pip3 install -r requirements.txt` to install `requests` and `python-dotenv`
5. Run `python3 main.py`
6. Follow the instructions in the terminal

# API endpoints used

## /search/repositories

This endpoint retrieves first 1000 results of the search by keywords provided in 
`q` parameter of the request. `per_page` and `page` parameters can also be used for pagination.

## /repos/{owner}/{repo}

This endpoint retrieves info about repository identified by its name and author

## /repos/{owner}/{repo}/{commits}

This endpoint retrieves all the commits found in the repo identified by its name and author.
`per_page` and `page` parameters can also be used for pagination.

## /repos/{owner}/{repo}/{contents}/{+path}

This endpoint retrieves all the contents found in the repo identified by its name and author, 
folder identified by its absolute path (root folder if empty path is provided).
`per_page` and `page` parameters can also be used for pagination.

# Research conclusion

GitHub provides a very easy-to-use and well documented REST API allowing you to extract needed data without
much pain and managing rate limits with easy due to all necessary data provided in the response headers
