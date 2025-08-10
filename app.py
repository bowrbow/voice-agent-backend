from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import time
from datetime import datetime
from functools import wraps
import threading
from flask_swagger_ui import get_swaggerui_blueprint

# Initialize Flask app
app = Flask(__name__)
# Enable CORS for all routes - critical for Elevenlabs to call your API
CORS(app)

# Configure Swagger UI
SWAGGER_URL = '/docs'  # URL for exposing Swagger UI
API_URL = '/static/swagger.json'  # Our API url (can be a local file or url)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Voice Agent API Documentation"}
)

# Register blueprint at URL
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Ensure the static folder exists
os.makedirs(os.path.join(app.root_path, 'static'), exist_ok=True)

# Create the swagger.json file (weather/time removed)
swagger_json = {
    "openapi": "3.0.0",
    "info": {
        "title": "Voice Agent Backend API",
        "description": "API for Elevenlabs Voice Agents",
        "version": "1.0.0"
    },
    "servers": [{"url": "/"}],
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
    },
    "security": [{"ApiKeyAuth": []}],
    "paths": {
        "/search": {
            "post": {
                "summary": "Search for information",
                "description": "Search the web for information on a given topic",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query"
                                    }
                                },
                                "required": ["query"]
                            },
                            "example": {
                                "query": "voice agents"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful search",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "results": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Unauthorized - Invalid or missing API key"},
                    "429": {"description": "Too Many Requests - Rate limit exceeded"}
                }
            }
        }
    }
}

# Write the swagger.json file
with open(os.path.join(app.root_path, 'static', 'swagger.json'), 'w') as f:
    json.dump(swagger_json, f)

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.lock = threading.Lock()
    
    def is_rate_limited(self, key, limit=20, period=60):
        with self.lock:
            now = time.time()
            # Clean up expired entries
            self.requests = {k: v for k, v in self.requests.items() if v['timestamp'] > now - period}
            # If key doesn't exist yet
            if key not in self.requests:
                self.requests[key] = {'count': 1, 'timestamp': now}
                return False
            # Check if limit exceeded
            if self.requests[key]['count'] >= limit:
                return True
            # Increment counter
            self.requests[key]['count'] += 1
            return False

# Initialize rate limiter
rate_limiter = RateLimiter()

# API Key validation decorator
def validate_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        valid_api_keys = os.environ.get('ALLOWED_API_KEYS', '').split(',')
        if not api_key or api_key not in valid_api_keys:
            print(f"❌ Invalid API key attempt: {api_key if api_key else 'No key provided'}")
            return jsonify({
                "success": False,
                "error": "Invalid or missing API key. Join our community to get access: https://www.skool.com/ai-freedom-finders"
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# Rate limiting decorator
def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key') or request.remote_addr
        if rate_limiter.is_rate_limited(key):
            print(f"⚠️ Rate limit exceeded for: {key}")
            return jsonify({
                "success": False,
                "error": "Rate limit exceeded. Please try again later or upgrade your plan."
            }), 429
        return f(*args, **kwargs)
    return decorated_function

# Configure custom logging
def log_divider(title):
    line_length = 80
    padding = (line_length - len(title) - 2) // 2
    print("\n" + "=" * padding + f" {title} " + "=" * padding + "\n")

def log_request(endpoint, data):
    log_divider(f"INCOMING REQUEST TO {endpoint}")
    print(f"Timestamp: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    print(f"Request data: {json.dumps(data, indent=2)}")

def log_api_call(service, url, params=None):
    log_divider(f"CALLING {service} API")
    print(f"URL: {url}")
    if params:
        print(f"Parameters: {json.dumps(params, indent=2)}")

def log_api_response(service, response_data, status_code):
    log_divider(f"{service} API RESPONSE")
    print(f"Status code: {status_code}")
    print(f"Response: {json.dumps(response_data, indent=2) if isinstance(response_data, dict) else str(response_data)[:500]}")

def log_response(endpoint, response_data, success):
    log_divider(f"OUTGOING RESPONSE FROM {endpoint}")
    print(f"Success: {success}")
    print(f"Response data: {json.dumps(response_data, indent=2)}")

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify the service is running"""
    print("\n✅ Health check endpoint called")
    return jsonify({"status": "healthy", "message": "Voice agent backend is running!"})

@app.route('/search', methods=['POST'])
@validate_api_key
@rate_limit
def web_search():
    """Web search endpoint that queries Wikipedia and parses results"""
    try:
        data = request.json
        log_request("SEARCH", data)
        
        if not data or 'query' not in data:
            error_response = {"success": False, "error": "Please provide a search query"}
            log_response("SEARCH", error_response, False)
            return jsonify(error_response), 400
        
        query = data['query']
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&utf8="
        log_api_call("WIKIPEDIA", wiki_url)
        
        start_time = time.time()
        response = requests.get(
            wiki_url,
            headers={"User-Agent": "VoiceAgentDemo/1.0"}
        )
        api_time = time.time() - start_time
        
        log_api_response("WIKIPEDIA", response.json(), response.status_code)
        
        if response.status_code != 200:
            error_response = {
                "success": False,
                "error": f"Search API returned status code {response.status_code}"
            }
            log_response("SEARCH", error_response, False)
            return jsonify(error_response), 500
        
        results = response.json()
        voice_response = "Here's what I found: "
        
        if results.get("query") and results["query"].get("search") and len(results["query"]["search"]) > 0:
            search_results = results["query"]["search"][:2]
            for i, result in enumerate(search_results):
                if i == 0:
                    voice_response += f"{result.get('snippet', '')}. "
                else:
                    voice_response += f"I also found that {result.get('snippet', '')}. "
            voice_response = voice_response.replace("</span>", "")
            voice_response = voice_response.replace("<span class=\"searchmatch\">", "")
        else:
            voice_response = "I couldn't find any information about that. Would you like to try a different search?"
        
        success_response = {"success": True, "results": voice_response}
        log_response("SEARCH", {"success": True, "results": voice_response[:100] + "..." if len(voice_response) > 100 else voice_response}, True)
        print(f"⏱️ Wikipedia API call took {api_time:.2f} seconds")
        return jsonify(success_response)
    
    except Exception as e:
        print(f"❌ ERROR in search endpoint: {str(e)}")
        error_response = {
            "success": False,
            "error": "Sorry, I had trouble searching for that information."
        }
        log_response("SEARCH", error_response, False)
        return jsonify(error_response), 500

# Add simple landing page that redirects to docs
@app.route('/', methods=['GET'])
def index():
    """Landing page that redirects to interactive docs"""
    return '''
    <html>
        <head>
            <title>Voice Agent Backend API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }
                h1 { color: #333; }
                .card { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }
                .button { display: inline-block; background: #0066cc; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px; }
                .note { background: #ffffcc; padding: 10px; border-left: 4px solid #ffcc00; text-align: left; }
            </style>
        </head>
        <body>
            <h1>Voice Agent Backend API</h1>
            <div class="card">
                <p>This API provides functionality for Elevenlabs voice agents, including a web search endpoint.</p>
                <a href="/docs" class="button">Interactive API Documentation</a>
            </div>
            
            <div class="note">
                <p><strong>Note:</strong> API access requires an API key. Contact the developer to get access.</p>
                <p>All endpoints are rate limited to 20 requests per minute per API key.</p>
            </div>
        </body>
    </html>
    '''

if __name__ == '__main__':
    # Print startup banner
    print("\n" + "=" * 80)
    print(" 🎙️  VOICE AGENT BACKEND SERVER STARTING  🎙️ ")
    print("=" * 80)
    print(" ℹ️  This server provides API endpoints for Elevenlabs voice agents")
    print(" 🔐 API Key Authentication enabled")
    print(" ⏱️  Rate limiting enabled (20 requests per minute per key)")
    print(" 📚 Interactive API docs available at /docs")
    print(" 🔍 /search - Search for information using Wikipedia")
    print("=" * 80 + "\n")
    
    # Get port from environment variable (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port)
