# GitHub Gists API

This program make a API call aganist Github and get the public gists for the user, this program also handles cacheing and Pagination 

## Requirements

- Python 3.13
- Docker, optional for running locally

## To Run locally,

Navigate to the source code folder in terminal and run following command, this should start the server with http://localhost:8080/

```bash
python app.py
```

To test the server running call the API using folliwng curl command:

```bash
curl http://localhost:8080/octocat
```
## Features covered in this API

- Pagination to collect results across GitHub pages
- In-memory caching for 60 seconds per username

## Run tests

```bash
python -m unittest discover -s tests -v
```

For integration tests require a running API, start `python app.py` in another terminal first.

## to build Docker container use following command :

```bash
docker build -t rv-gists-api .
docker run --rm -p 8080:8080 rv-gists-api
```

The container listens on port 8080 and packages only the API.

## Verification

Local application testing completed. Docker build and container startup remain unverified because Docker installation failed on the development machine.

