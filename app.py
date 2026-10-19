import json
import time
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):

        print(f"Received GET request for {self.path}")

        username = self.path.strip("/")

        if not username:
            self.generate_json(
                400,  # HTTP 400 means the request is invalid.
                {"error": "Enter a username in the URL"}  # Error response data.
            )
            return

        github_url = (f"https://api.github.com/users/{username}/gists")

        request = Request(
            github_url, 
            headers={
                "Accept": "application/vnd.github.v3+json",
                "user-agent": "RV Http Client"
                    
            }
        )

        cache_key = username.lower()  # Use lowercase for case-insensitive caching
        cached = CACHE.get(cache_key)  # Check if the response is cached and still valid
        if cached is not None:
            cache_duration = time.monotonic() - cached["saved_at"]
            if cache_duration < CACHE_TTL:
                print(f"Returning cached response for {username}")
                self.generate_json(
                    200,
                    cached["gists"]
                )
                return
            else:
                print(f"Cache expired for {username}, fetching new data")
                del CACHE[cache_key]
        print(f"caching missing or expired for {username}, fetching new data")

        try:
            #this variables used in loop to store the public gists and control the pagination
            public_gists = []
            page = 1
            page_size = 100
            while True: # while loop to load the data 

                paginated_url = (
                    f"{github_url}?per_page={page_size}&page={page}" # setting pagination rule
                )
                request = Request(
                    paginated_url, 
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "user-agent": "RV Http Client"
                    }
                )
        
                with urlopen(request, timeout=10) as github_response:
                    gists = json.load(
                        github_response
                    )
                print(f"Page {page}: received {len(gists)} Gists")

                public_gists.extend(
                    gist
                    for gist in gists
                    if gist.get("public")is True
                )
                
                if(len(gists) < page_size):
                    break   

                page += 1

            self.generate_json(
                200,
                public_gists
            )
            # Cache the response
            CACHE[cache_key] = {
                "gists": public_gists,
                "saved_at": time.monotonic()
            }
        except HTTPError as error:
            self.generate_json(
                error.code,
                {"error": f"HTTP Error: {error.reason}"}
            )
        except URLError as error:
            self.generate_json(
                500,
                {"error": f"URL Error: {error.reason}"}
            )
        except(TimeoutError, socket.timeout) as error:
            self.generate_json(
                504,
                {"error": "Request timed out"}
            )

    def generate_json(self, status_code, result):

        response = json.dumps(result).encode("utf-8")

        self.send_response(status_code)

        self.send_header("Content-Type", "application/json")
        self.send_header("content-length", str(len(response)))
        self.end_headers()  
        self.wfile.write(response)

# This dictionary will store the cached responses for each username, along with their timestamps. The keys will be the usernames, and the values will be tuples containing the response data and the timestamp of when it was cached.
CACHE = {}
CACHE_TTL = 60

if __name__ == "__main__": # start the server and listen for incoming requests
    server = HTTPServer(("0.0.0.0", 8080), RequestHandler)

    print("Server started on port 8080")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
    finally:
        server.server_close()
