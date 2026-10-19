import io
import json
import unittest
from unittest.mock import patch, Mock
from urllib.error import HTTPError, URLError

import app

def github_response(gists):
    return io.BytesIO(json.dumps(gists).encode('utf-8')) # Mocking the response from GitHub API

class HTTPRequestHandelerTest(unittest.TestCase):

    def setUp(self):

        print("\nSetting up test...")
        
        app.CACHE.clear()  # Clear the cache before each test
        self.addCleanup(app.CACHE.clear)  # Ensure cache is cleared after each test

        self.handler = object.__new__(app.RequestHandler)  # Create an instance of HTTPRequestHandler without calling __init__
        self.handler.path = "/octocat"  # Set the path to /gists for testing

        self.handler.generate_json = Mock()  # Mock the generate_json method to capture its calls

        self.gist = {
            "id": "1",
            "description": "example Gist",
            "public": True,
        }

        self.urlopen = self.enterContext(patch("app.urlopen")) # Patch the urlopen function in app module to mock HTTP requests

        # Control time so cache tests need no waiting.
        self.clock = self.enterContext(
            patch("app.time.monotonic", return_value=1000)
        )

        # Keep the cache duration predictable during tests.
        self.enterContext(
            patch("app.CACHE_TTL", 60)
        )
    def test_health_endpoint(self):
        self.handler.path = "/health"

        self.handler.do_GET()

        self.handler.generate_json.assert_called_once_with(
            200, {"status": "healthy"})
        self.urlopen.assert_not_called()
        
    def test_empty_username(self):
        print("\nTesting empty username returns 400...")
        self.handler.path = "/"
        self.handler.do_GET()
        self.handler.generate_json.assert_called_once_with(
            400, {"error": "Enter a username in the URL"}
        )
        self.urlopen.assert_not_called()  # Ensure that urlopen was not called since the username is empty

    def test_gists_and_cache_result(self):
        print("\nTesting gists and cache result...")
        self.urlopen.return_value = github_response([self.gist])  

        self.handler.do_GET()  

        self.handler.generate_json.assert_called_once_with(
            200, [self.gist]
        )  

        self.assertIn("octocat", app.CACHE)  # Check that the response is cached
        self.assertEqual(app.CACHE["octocat"]["gists"], [self.gist])  # Check that the cached gists are correct
        self.assertEqual(app.CACHE["octocat"]["saved_at"], 1000)  # Check that the saved_at timestamp is correct

    def test_cache_expiires_at_60_seconds(self):
        print("\nTesting cache expires at 60 seconds...")
        app.CACHE["octocat"] = {
            "gists": [self.gist],
            "saved_at": 900
        } # Pre-populate the cache with a saved_at timestamp of 900

        self.urlopen.return_value = github_response([self.gist])  # Mock the urlopen response to return the same gist

        self.handler.do_GET()  

        self.urlopen.assert_called_once()  # Ensure that urlopen was called since the cache expired

        self.handler.generate_json.assert_called_once_with(
            200, [self.gist]
        )
        self.assertEqual(app.CACHE["octocat"]["saved_at"], 1000)  # Check that the saved_at timestamp is updated to 1000  

    def test_request_has_correct_headers_and_timeout(self):
        print("\nTesting request has correct headers...")
        self.urlopen.return_value = github_response([self.gist])  # Mock the urlopen response to return the same gist

        self.handler.do_GET()  

        self.urlopen.assert_called_once()  # Ensure that urlopen was called

        args, kwargs = self.urlopen.call_args    # Get the arguments and keyword arguments of the call to urlopen
        request_arg = args[0]  # Get the first argument of the call to urlopen, which is the Request object

        self.assertEqual(request_arg.get_header("Accept"), "application/vnd.github.v3+json")  # Check that the Accept header is correct
        self.assertEqual(request_arg.get_header("User-agent"), "RV Http Client")  #Check that the user-agent header is correct
        self.assertEqual(request_arg.full_url, "https://api.github.com/users/octocat/gists?per_page=100&page=1")  # Check that the URL is correct   
        self.assertEqual(kwargs.get("timeout"), 10)  # Check that the timeout is set to 10 seconds

    def test_pagination(self):
            print("\nTesting pagination...")
            first_page = [
                {"id": str(i), "public": True}
                for i in range(100)
            ]
            second_page = [self.gist]
    
            # Each urlopen call receives the next response.
            self.urlopen.side_effect = [
                github_response(first_page),
                github_response(second_page)
            ]
    
            self.handler.do_GET()
    
            expected = first_page + second_page
    
            self.handler.generate_json.assert_called_once_with(
                200, expected
            )
            self.assertEqual(
                app.CACHE["octocat"]["gists"], expected
            )
    
            urls = [
                call.args[0].full_url
                for call in self.urlopen.call_args_list
            ]
    
            self.assertEqual(urls, [
                "https://api.github.com/users/octocat/gists"
                "?per_page=100&page=1",
                "https://api.github.com/users/octocat/gists"
                "?per_page=100&page=2"
            ])
    def test_http_errors_not_cached(self):
        print("\nTesting errors are not cached...")
        self.urlopen.side_effect = HTTPError(
            url="https://api.github.com/users/octocat/gists",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None
        )

        self.handler.do_GET()

        self.handler.generate_json.assert_called_once_with(
            404, {"error": "HTTP Error: Not Found"}
        )

        self.assertNotIn("octocat", app.CACHE)  # Ensure that the error response is not cached

    def test_url_errors_not_cached(self):
        print("\nTesting URL errors are not cached...")
        self.urlopen.side_effect = URLError("Offline")

        self.handler.do_GET()

        self.handler.generate_json.assert_called_once_with(
            500, {"error": "URL Error: Offline"}
        )
        self.assertNotIn("octocat", app.CACHE)  # Ensure that the error response is not cached

    def test_only_public_gists_are_returned(self):
        print("\nTesting only public gists are returned...")
        gists = [
            {"id": "1", "public": True},
            {"id": "2", "public": False},
            {"id": "3", "public": True}
        ]
        self.urlopen.return_value = github_response(gists)

        self.handler.do_GET()

        expected = [
            {"id": "1", "public": True},
            {"id": "3", "public": True}
        ]

        self.handler.generate_json.assert_called_once_with(
            200, expected
        )
        print(app.CACHE["octocat"]["gists"])
        self.assertEqual(app.CACHE["octocat"]["gists"], expected)  # Ensure that only public gists are cached
if __name__ == "__main__":
    unittest.main()

