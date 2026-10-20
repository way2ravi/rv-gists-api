import json
import time
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = logging.getLogger("rv-gists-api")

class RequestHandler(BaseHTTPRequestHandler):
    def process_get(self):
        if self.path == "/health":
            self.generate_json(200, {"status": "healthy"})
            return

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
                self.cache_hit = True
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
        
                upstream_start = time.perf_counter()

                with urlopen(request, timeout=10) as github_response:
                    gists = json.load(github_response)

                upstream_duration_ms = round(
                    (time.perf_counter() - upstream_start) * 1000,
                    2
                )

                logger.info(json.dumps({
                    "event": "github_api_call",
                    "username": username,
                    "page": page,
                    "duration_ms": upstream_duration_ms,
                    "gist_count": len(gists)
                }))
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

        self.response_status = status_code
        self.send_response(status_code)

        self.send_header("Content-Type", "application/json")
        self.send_header("content-length", str(len(response)))
        self.end_headers()  
        self.wfile.write(response)

    # def handle_one_request(self):
    #     start_time = time.perf_counter()

    #     try:
    #         super().handle_one_request()
    #     finally:
    #         duration_ms = round(
    #             (time.perf_counter() - start_time) * 1000,
    #             2
    #         )

    #         logger.info(json.dumps({
    #             "event": "request_completed",
    #             "duration_ms": duration_ms
    #         }))
    def do_GET(self):
        start_time = time.perf_counter()
        self.response_status = 500
        self.cache_hit = False

        try:
            self.process_get()
        finally:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2
            )

            logger.info(json.dumps({
                "event": "http_request",
                "method": "GET",
                "path": self.path,
                "status_code": self.response_status,
                "duration_ms": duration_ms,
                "cache_hit": self.cache_hit
            }))
    def log_message(self, format, *args):
        pass

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
