from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

# Initialize Flask app
app = Flask(__name__)
# Enable CORS for all routes - critical for Elevenlabs to call your API
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify the service is running"""
    return jsonify({"status": "healthy", "message": "Voice agent backend is running!"})

@app.route('/search', methods=['POST'])
def web_search():
    """Web search endpoint that queries Google and parses results"""
    try:
        # Get the search query from the request
        data = request.json
        if not data or 'query' not in data:
            return jsonify({
                "success": False, 
                "error": "Please provide a search query"
            }), 400
        
        query = data['query']
        
        # Use a more reliable approach - searching Wikipedia
        response = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&utf8=",
            headers={"User-Agent": "VoiceAgentDemo/1.0"}
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Search API returned status code {response.status_code}"
            }), 500
        
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
        
        return jsonify({
            "success": True,
            "results": voice_response
        })
    
    except Exception as e:
        print(f"Error processing search request: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Sorry, I had trouble searching for that information."
        }), 500

@app.route('/weather', methods=['POST'])
def weather():
    """Weather endpoint using OpenWeatherMap API"""
    try:
        # Get the location from the request
        data = request.json
        if not data or 'location' not in data:
            return jsonify({
                "success": False, 
                "error": "Please provide a location"
            }), 400
        
        location = data['location']
        
        # Get API key from environment variable
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "Weather API key not configured"
            }), 500
        
        # Call OpenWeatherMap API
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Weather API returned status code {response.status_code}"
            }), 500
        
        # Parse weather data
        weather_data = response.json()
        
        # Format for voice response
        temp = weather_data["main"]["temp"]
        condition = weather_data["weather"][0]["description"]
        city = weather_data["name"]
        
        voice_response = f"The current weather in {city} is {condition} with a temperature of {temp} degrees Celsius."
        
        return jsonify({
            "success": True,
            "results": voice_response
        })
    
    except Exception as e:
        print(f"Error processing weather request: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Sorry, I had trouble getting the weather information."
        }), 500
    
@app.route('/time', methods=['POST'])
def world_clock():
    """Get the current time in any location around the world"""
    try:
        data = request.json
        if not data or 'location' not in data:
            return jsonify({
                "success": False, 
                "error": "Please provide a location"
            }), 400
        
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
        
        # Try to find the timezone
        from datetime import datetime
        import pytz
        
        if location_lower in timezone_map:
            timezone_str = timezone_map[location_lower]
            timezone = pytz.timezone(timezone_str)
            current_time = datetime.now(timezone)
            
            # Format time nicely
            formatted_time = current_time.strftime("%I:%M %p on %A, %B %d, %Y")
            
            return jsonify({
                "success": True,
                "results": f"The current time in {location} is {formatted_time}."
            })
        else:
            # Try to guess the timezone using pytz
            for tz_name in pytz.all_timezones:
                if location_lower in tz_name.lower():
                    timezone = pytz.timezone(tz_name)
                    current_time = datetime.now(timezone)
                    formatted_time = current_time.strftime("%I:%M %p on %A, %B %d, %Y")
                    
                    return jsonify({
                        "success": True,
                        "results": f"The current time in {location} is {formatted_time}."
                    })
            
            return jsonify({
                "success": False,
                "error": f"I couldn't find a timezone for {location}. Try a major city name instead."
            }), 404
            
    except Exception as e:
        print(f"Error processing time request: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Sorry, I had trouble getting the time: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Get port from environment variable (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)