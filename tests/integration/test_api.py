
import json
import os
import unittest
from urllib.request import urlopen


class APIIntegrationTest(unittest.TestCase):

    def test_octocat_returns_gists(self):
        print("\nTesting octocat returns gists...")

        base_url = os.environ.get("API_BASE_URL", "http://localhost:8080").rstrip("/")  

        with urlopen(f"{base_url}/octocat", timeout=30) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_type(), "application/json")

            gists = json.loads(response.read().decode("utf-8"))

            self.assertIsInstance(gists, list)  # Ensure the response is a list

            for gist in gists:
                self.assertIsInstance(gist, dict)  # Ensure each gist is a dictionary
                self.assertIn("id", gist)  # Ensure each gist has an "id" field
                self.assertIn("description", gist)  # Ensure each gist has a "description" field
                self.assertIn("public", gist)  # Ensure each gist has a "public" field
                self.assertIsInstance(gist["id"], str) # Ensure the "id" field is a string
                self.assertTrue(gist["id"]) # Ensure the "id" field is not empty

if __name__ == "__main__":
    unittest.main()

