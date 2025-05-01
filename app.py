from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import time
from datetime import datetime
import pytz
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
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Voice Agent API Documentation"
    }
)

# Register blueprint at URL
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Ensure the static folder exists
os.makedirs(os.path.join(app.root_path, 'static'), exist_ok=True)

# Create the swagger.json file
swagger_json = {
    "openapi": "3.0.0",
    "info": {
        "title": "Voice Agent Backend API",
        "description": "API for Elevenlabs Voice Agents",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "/"
        }
    ],
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
    },
    "security": [
        {
            "ApiKeyAuth": []
        }
    ],
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
                                        "success": {
                                            "type": "boolean"
                                        },
                                        "results": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized - Invalid or missing API key"
                    },
                    "429": {
                        "description": "Too Many Requests - Rate limit exceeded"
                    }
                }
            }
        },
        "/weather": {
            "post": {
                "summary": "Get current weather",
                "description": "Get current weather for a location",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "The city or location name"
                                    }
                                },
                                "required": ["location"]
                            },
                            "example": {
                                "location": "London"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful weather retrieval",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {
                                            "type": "boolean"
                                        },
                                        "results": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized - Invalid or missing API key"
                    },
                    "429": {
                        "description": "Too Many Requests - Rate limit exceeded"
                    }
                }
            }
        },
        "/time": {
            "post": {
                "summary": "Get current time",
                "description": "Get the current time in any location around the world",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "The city or location name"
                                    }
                                },
                                "required": ["location"]
                            },
                            "example": {
                                "location": "Tokyo"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful time retrieval",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {
                                            "type": "boolean"
                                        },
                                        "results": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized - Invalid or missing API key"
                    },
                    "429": {
                        "description": "Too Many Requests - Rate limit exceeded"
                    }
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
                self.requests[key] = {
                    'count': 1,
                    'timestamp': now
                }
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
        # Get API key from request header
        api_key = request.headers.get('X-API-Key')
        
        # Get valid API keys from environment variable
        valid_api_keys = os.environ.get('ALLOWED_API_KEYS', '').split(',')
        
        # Check if API key is valid
        if not api_key or api_key not in valid_api_keys:
            print(f"❌ Invalid API key attempt: {api_key if api_key else 'No key provided'}")
            return jsonify({
                "success": False,
                "error": "Invalid or missing API key. Join our community to get access: https://example.com/community"
            }), 401
        
        # If API key is valid, proceed
        return f(*args, **kwargs)
    return decorated_function

# Rate limiting decorator
def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key for rate limiting
        key = request.headers.get('X-API-Key') or request.remote_addr
        
        # Check if rate limited
        if rate_limiter.is_rate_limited(key):
            print(f"⚠️ Rate limit exceeded for: {key}")
            return jsonify({
                "success": False,
                "error": "Rate limit exceeded. Please try again later or upgrade your plan."
            }), 429
        
        # If not rate limited, proceed
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
    print(f"Response: {json.dumps(response_data, indent=2) if isinstance(response_data, dict) else response_data[:500]}")

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
        # Log incoming request
        data = request.json
        log_request("SEARCH", data)
        
        if not data or 'query' not in data:
            error_response = {"success": False, "error": "Please provide a search query"}
            log_response("SEARCH", error_response, False)
            return jsonify(error_response), 400
        
        query = data['query']
        
        # Build Wikipedia API URL
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&utf8="
        
        # Log API call
        log_api_call("WIKIPEDIA", wiki_url)
        
        # Call Wikipedia API
        start_time = time.time()
        response = requests.get(
            wiki_url,
            headers={"User-Agent": "VoiceAgentDemo/1.0"}
        )
        api_time = time.time() - start_time
        
        # Log API response
        log_api_response("WIKIPEDIA", response.json(), response.status_code)
        
        if response.status_code != 200:
            error_response = {
                "success": False,
                "error": f"Search API returned status code {response.status_code}"
            }
            log_response("SEARCH", error_response, False)
            return jsonify(error_response), 500
        
        # Parse the results
        results = response.json()
        
        # Format results for voice response
        voice_response = "Here's what I found: "
        
        # Get search results
        if results.get("query") and results["query"].get("search") and len(results["query"]["search"]) > 0:
            # Get first 2 results
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
        
        # Log successful response
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

@app.route('/weather', methods=['POST'])
@validate_api_key
@rate_limit
def weather():
    """Weather endpoint using OpenWeatherMap API"""
    try:
        # Log incoming request
        data = request.json
        log_request("WEATHER", data)
        
        if not data or 'location' not in data:
            error_response = {"success": False, "error": "Please provide a location"}
            log_response("WEATHER", error_response, False)
            return jsonify(error_response), 400
        
        location = data['location']
        
        # Get API key from environment variable
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        
        if not api_key:
            error_response = {"success": False, "error": "Weather API key not configured"}
            log_response("WEATHER", error_response, False)
            return jsonify(error_response), 500
        
        # Build OpenWeatherMap API URL
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        
        # Log API call (hide API key for security)
        log_api_call("OPENWEATHERMAP", weather_url.replace(api_key, "API_KEY_HIDDEN"))
        
        # Call OpenWeatherMap API
        start_time = time.time()
        response = requests.get(weather_url)
        api_time = time.time() - start_time
        
        # Log API response
        log_api_response("OPENWEATHERMAP", response.json(), response.status_code)
        
        if response.status_code != 200:
            error_response = {
                "success": False,
                "error": f"Weather API returned status code {response.status_code}"
            }
            log_response("WEATHER", error_response, False)
            return jsonify(error_response), 500
        
        # Parse weather data
        weather_data = response.json()
        
        # Format for voice response
        temp = weather_data["main"]["temp"]
        condition = weather_data["weather"][0]["description"]
        city = weather_data["name"]
        
        voice_response = f"The current weather in {city} is {condition} with a temperature of {temp} degrees Celsius."
        
        # Log successful response
        success_response = {"success": True, "results": voice_response}
        log_response("WEATHER", success_response, True)
        print(f"⏱️ Weather API call took {api_time:.2f} seconds")
        
        return jsonify(success_response)
    
    except Exception as e:
        print(f"❌ ERROR in weather endpoint: {str(e)}")
        error_response = {
            "success": False,
            "error": "Sorry, I had trouble getting the weather information."
        }
        log_response("WEATHER", error_response, False)
        return jsonify(error_response), 500
    
@app.route('/time', methods=['POST'])
@validate_api_key
@rate_limit
def world_clock():
    """Get the current time in any location around the world"""
    try:
        # Log incoming request
        data = request.json
        log_request("TIME", data)
        
        if not data or 'location' not in data:
            error_response = {"success": False, "error": "Please provide a location"}
            log_response("TIME", error_response, False)
            return jsonify(error_response), 400
        
        location = data['location']
        
        # Map common city names to time zones
        timezone_map = {
            'london': 'Europe/London',
            'new york': 'America/New_York',
            'los angeles': 'America/Los_Angeles',
            'tokyo': 'Asia/Tokyo',
            'sydney': 'Australia/Sydney',
            'paris': 'Europe/Paris',
            'berlin': 'Europe/Berlin',
            'beijing': 'Asia/Shanghai',
            'dubai': 'Asia/Dubai',
            'rio': 'America/Sao_Paulo',
            'moscow': 'Europe/Moscow',
            'hong kong': 'Asia/Hong_Kong',
            'singapore': 'Asia/Singapore',
            'mumbai': 'Asia/Kolkata',
            'cairo': 'Africa/Cairo',
            'johannesburg': 'Africa/Johannesburg',
            'rome': 'Europe/Rome',
            'bangkok': 'Asia/Bangkok',
            'toronto': 'America/Toronto',
            'mexico city': 'America/Mexico_City',
            'san francisco': 'America/Los_Angeles',
            'chicago': 'America/Chicago',
            'istanbul': 'Europe/Istanbul',
            'madrid': 'Europe/Madrid',
            'amsterdam': 'Europe/Amsterdam',
            'stockholm': 'Europe/Stockholm',
            'seoul': 'Asia/Seoul'
        }
        
        # Handle case sensitivity
        location_lower = location.lower()
        
        # Log timezone lookup process
        start_time = time.time()
        log_divider("TIMEZONE LOOKUP")
        
        found_timezone = None
        timezone_source = None
        
        # Try to find the timezone in our map
        if location_lower in timezone_map:
            timezone_str = timezone_map[location_lower]
            found_timezone = timezone_str
            timezone_source = "predefined map"
            print(f"✅ Found timezone for '{location}' in predefined map: {timezone_str}")
        else:
            # Try to guess the timezone using pytz
            print(f"⚠️ '{location}' not found in predefined map, searching pytz timezones...")
            
            for tz_name in pytz.all_timezones:
                if location_lower in tz_name.lower():
                    found_timezone = tz_name
                    timezone_source = "pytz search"
                    print(f"✅ Found matching timezone in pytz: {tz_name}")
                    break
            
            if not found_timezone:
                print(f"❌ No matching timezone found for '{location}'")
        
        lookup_time = time.time() - start_time
        print(f"⏱️ Timezone lookup took {lookup_time:.2f} seconds")
        
        if found_timezone:
            timezone = pytz.timezone(found_timezone)
            current_time = datetime.now(timezone)
            
            # Format time nicely
            formatted_time = current_time.strftime("%I:%M %p on %A, %B %d, %Y")
            
            voice_response = f"The current time in {location} is {formatted_time}."
            
            # Log successful response
            success_response = {"success": True, "results": voice_response}
            log_response("TIME", success_response, True)
            print(f"🌐 Timezone: {found_timezone} (found via {timezone_source})")
            
            return jsonify(success_response)
        else:
            error_response = {
                "success": False,
                "error": f"I couldn't find a timezone for {location}. Try a major city name instead."
            }
            log_response("TIME", error_response, False)
            return jsonify(error_response), 404
            
    except Exception as e:
        print(f"❌ ERROR in time endpoint: {str(e)}")
        error_response = {
            "success": False,
            "error": f"Sorry, I had trouble getting the time: {str(e)}"
        }
        log_response("TIME", error_response, False)
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
                <p>This API provides functionality for Elevenlabs voice agents including web search, weather information, and world clock.</p>
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
    print(" ⛅ /weather - Get weather information for any location")
    print(" 🕒 /time - Get current time in any timezone")
    print("=" * 80 + "\n")
    
    # Get port from environment variable (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port)