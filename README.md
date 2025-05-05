# Voice Agent Backend Server

A simple yet powerful backend server designed to add custom capabilities to Elevenlabs voice agents. This project gives your voice agents the ability to search the web, check the weather, and tell the time in any location around the world.

## 📋 Features

- 🔍 **Web Search**: Connected to Wikipedia for instant information lookup
- ⛅ **Weather Information**: Real-time weather data using OpenWeatherMap
- 🕒 **World Clock**: Accurate time information for any city or timezone
- 🔐 **API Key Protection**: Secure endpoints with API key authentication
- 📊 **Rate Limiting**: Prevents abuse with 20 requests/minute limit
- 📚 **Interactive Docs**: Built-in Swagger UI for easy testing

## 🚀 Getting Started

### Prerequisites

Before you begin, you'll need:

- A GitHub account (for forking this repository)
- An [OpenWeatherMap API key](https://home.openweathermap.org/users/sign_up) (free tier works fine)
- Basic understanding of API keys and environment variables

### Forking the Repository

1. Click the "Fork" button at the top right of this repository
2. Wait for GitHub to create a copy in your account
3. You now have your own copy of the code to customize!

## 🛠️ Local Setup

Want to run the server on your own computer for testing? Follow these steps:

### Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/voice-agent-backend.git
cd voice-agent-backend
```

### Set Up Environment

1. Create a `.env` file in the root directory:

```
# API Keys
OPENWEATHER_API_KEY=your_openweather_api_key_here
ALLOWED_API_KEYS=key1,key2,key3

# Server Configuration
PORT=5000
```

2. Install dependencies:

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. Run the server:

```bash
python app.py
```

4. Test the server by visiting `http://localhost:5000/docs` in your browser

## ☁️ Deploying to Render

Follow these steps to deploy your backend to Render's free hosting:

1. Sign up for a [Render account](https://render.com/) if you don't have one

2. Create a new Web Service:
   - Click "New" and select "Web Service"
   - Connect to your GitHub repository
   - Name your service (e.g., "my-voice-agent-backend")

3. Configure the deploy settings:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

4. Add environment variables:
   - Click "Environment" to expand the section
   - Add the following variables:
     - `OPENWEATHER_API_KEY`: Your OpenWeatherMap API key
     - `ALLOWED_API_KEYS`: Comma-separated list of API keys (e.g., `key1,key2,key3`)

5. Click "Create Web Service"

6. Wait for deployment to complete (this may take a few minutes)

7. Your API is now available at `https://your-service-name.onrender.com`!

> **Note**: Render's free tier will spin down your server after 15 minutes of inactivity. The first request after inactivity may take up to 30 seconds as the server "wakes up."

## 🔌 Connecting to Elevenlabs

Now that your backend is running, you can connect it to an Elevenlabs voice agent.

### ElevenLabs Agent Function Tools Configuration

Use these settings to add the function tools to your Elevenlabs agent:

#### Tool 1: Web Search
- Type: webhook
- Name: web_search
- Description: Search the web for information on a given topic
- API Schema:
  - URL: https://your-service-name.onrender.com/search
  - Method: POST
  - Request Headers:
    - X-API-Key: One of your API keys
    - Content-Type: application/json
  - Request Body Schema:
    - Type: object
    - Properties:
      - query:
        - Type: string
        - Description: The search query
    - Required: ["query"]
    - Description: Pass the user's search query to the web search API

#### Tool 2: Weather Information
- Type: webhook
- Name: get_weather
- Description: Get current weather for a location
- API Schema:
  - URL: https://your-service-name.onrender.com/weather
  - Method: POST
  - Request Headers:
    - X-API-Key: One of your API keys
    - Content-Type: application/json
  - Request Body Schema:
    - Type: object
    - Properties:
      - location:
        - Type: string
        - Description: The city or location name
    - Required: ["location"]
    - Description: Pass the user's requested location to the weather API

#### Tool 3: World Clock
- Type: webhook
- Name: get_time
- Description: Get the current time in any location around the world
- API Schema:
  - URL: https://your-service-name.onrender.com/time
  - Method: POST
  - Request Headers:
    - X-API-Key: One of your API keys
    - Content-Type: application/json
  - Request Body Schema:
    - Type: object
    - Properties:
      - location:
        - Type: string
        - Description: The city or location name
    - Required: ["location"]
    - Description: Pass the user's requested location to the time API

### Implementation Steps
To add these tools to your ElevenLabs agent:
1. Go to your agent configuration
2. Navigate to the Function Tools section
3. Add each tool using the "Custom Tool" > "Webhook" option
4. Configure each tool with the exact parameters listed above
5. Ensure your agent prompt instructs the agent to use these tools appropriately

### Agent Prompt Context
For reference, here's the relevant part of the agent prompt that instructs the agent on using these tools:

```
You are a helpful voice assistant with special capabilities. You can search for information on the web, check the current time in different cities around the world, and provide weather information.

You have three main abilities:
1. Web Search: You can find information about any topic using Wikipedia.
2. World Clock: You can tell the current time in any major city or time zone.
3. Weather Information: You can check the current weather conditions in different locations.

When a user asks for information that would benefit from one of these capabilities, use the appropriate function tool. Be conversational, helpful, and concise in your responses.

When a user asks any question which requires you to know what the current date is (someone's age, current affairs, time since historic events for example) ALWAYS use the GET TIME tool and use the current time to orientate your response.
```

## 📚 API Documentation

Once deployed, you can access the interactive API documentation at:
- `https://your-service-name.onrender.com/docs`

This Swagger UI interface allows you to:
- Explore all available endpoints
- Test each endpoint directly in your browser
- See required parameters and responses
- Authorize requests with your API key

### Authentication

All endpoints require an API key to be included in the request headers:
```
X-API-Key: your-api-key-here
```

### Rate Limiting

To prevent abuse, the API is rate-limited to 20 requests per minute per API key.

## 🛠️ Customization

Want to add your own endpoints or modify existing ones? Here are some ideas:

1. Add a News API endpoint
2. Create a translation service
3. Implement a joke generator
4. Build a currency converter

Check the source code for examples of how to structure new endpoints.

## ❓ Troubleshooting

### Common Issues

- **"API key invalid" error**: Make sure your API key is included in the `ALLOWED_API_KEYS` environment variable
- **Slow first request**: Render's free tier spins down after inactivity - the first request will "wake up" the server
- **Weather API errors**: Verify your OpenWeatherMap API key is correct and active

### Where to Find Logs

- In Render: Go to your service dashboard, click "Logs" in the left sidebar
- Locally: Check the terminal where you ran `python app.py`

## 🌐 Community Support

Join our Skool community for:
- One-on-one support
- Weekly live Q&A sessions
- Access to additional backend servers and utility tools
- Courses and resources for voice agent development

Visit: [AI Freedom Finders](https://www.skool.com/ai-freedom-finders)

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ by [Ben.AI](https://www.tiktok.com/@ai_entrepreneur_educator)
