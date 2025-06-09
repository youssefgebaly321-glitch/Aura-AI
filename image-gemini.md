# Gemini API with OpenAI Libraries Guide

## Overview

Gemini models are accessible using the OpenAI libraries (Python and TypeScript/JavaScript) along with the REST API. You can integrate Gemini models by updating just three lines of code and using your Gemini API key.

> **Note:** If you aren't already using the OpenAI libraries, we recommend calling the Gemini API directly.

## Quick Start Setup

### Basic Configuration

```python
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Explain to me how AI works"
        }
    ]
)

print(response.choices[0].message)
```

### What Changed? Just Three Lines!

1. **`api_key="GEMINI_API_KEY"`** - Replace with your actual Gemini API key from [Google AI Studio](https://ai.google.dev/aistudio)
2. **`base_url="https://generativelanguage.googleapis.com/v1beta/openai/"`** - Redirects OpenAI library requests to the Gemini API endpoint
3. **`model="gemini-2.0-flash"`** - Choose a compatible Gemini model

## Advanced Features

### Thinking (Reasoning Models)

Gemini 2.5 models are trained to think through complex problems, providing significantly improved reasoning capabilities. The OpenAI API offers three levels of thinking control:

- **"low"** - 1K thinking token budget
- **"medium"** - 8K thinking token budget  
- **"high"** - 24K thinking token budget
- **"none"** - Disable thinking

```python
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash-preview-05-20",
    reasoning_effort="low",  # Control thinking level
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Explain to me how AI works"
        }
    ]
)

print(response.choices[0].message)
```

### Streaming Responses

Real-time response streaming for better user experience:

```python
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta)
```

### Function Calling

Get structured data outputs from generative models:

```python
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. Chicago, IL",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        }
    }
]

messages = [{"role": "user", "content": "What's the weather like in Chicago today?"}]
response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

print(response)
```

## Multimodal Capabilities

### Image Understanding

Gemini models are natively multimodal with best-in-class performance on vision tasks:

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Encode your image
base64_image = encode_image("Path/to/agi/image.jpeg")

response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is in this image?",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
            ],
        }
    ],
)

print(response.choices[0])
```

### Image Generation

> **Note:** Image generation is only available in the paid tier.

```python
import base64
from openai import OpenAI
from PIL import Image
from io import BytesIO

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

response = client.images.generate(
    model="imagen-3.0-generate-002",
    prompt="a portrait of a sheepadoodle wearing a cape",
    response_format='b64_json',
    n=1,
)

for image_data in response.data:
    image = Image.open(BytesIO(base64.b64decode(image_data.b64_json)))
    image.show()
```

### Audio Understanding

Analyze and transcribe audio input:

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

with open("/path/to/your/audio/file.wav", "rb") as audio_file:
    base64_audio = base64.b64encode(audio_file.read()).decode('utf-8')

response = client.chat.completions.create(
    model="gemini-2.0-flash",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Transcribe this audio",
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": base64_audio,
                        "format": "wav"
                    }
                }
            ],
        }
    ],
)

print(response.choices[0].message.content)
```

## Structured Output

Generate JSON objects in any structure you define using Pydantic models:

```python
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.beta.chat.completions.parse(
    model="gemini-2.0-flash",
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {"role": "user", "content": "John and Susan are going to an AI conference on Friday."},
    ],
    response_format=CalendarEvent,
)

print(completion.choices[0].message.parsed)
```

## Available Models

### Text Models
- **gemini-2.0-flash** - Fast, efficient model for general tasks
- **gemini-2.5-flash-preview-05-20** - Advanced reasoning model with thinking capabilities

### Image Generation Models
- **imagen-3.0-generate-002** - High-quality image generation (paid tier only)

## Key Features Summary

| Feature | Support | Notes |
|---------|---------|-------|
| **Chat Completions** | ✅ | Standard conversational AI |
| **Streaming** | ✅ | Real-time response chunks |
| **Function Calling** | ✅ | Structured data extraction |
| **Vision** | ✅ | Image understanding and analysis |
| **Audio** | ✅ | Audio transcription and analysis |
| **Image Generation** | ✅ | Paid tier only |
| **Structured Output** | ✅ | Pydantic model integration |
| **Reasoning** | ✅ | Gemini 2.5 models with thinking control |

## Getting Started Checklist

1. **Get API Key** - Obtain your Gemini API key from [Google AI Studio](https://ai.google.dev/aistudio)
2. **Install Dependencies** - `pip install openai pillow pydantic` (add other dependencies as needed)
3. **Update Configuration** - Change three lines in your existing OpenAI code
4. **Test Basic Chat** - Start with simple text completion
5. **Explore Multimodal** - Try image, audio, and structured outputs
6. **Enable Advanced Features** - Experiment with reasoning and function calling

## Best Practices

- **API Key Security** - Store your API key securely using environment variables
- **Error Handling** - Implement proper error handling for API calls
- **Rate Limiting** - Be mindful of API rate limits and implement appropriate throttling
- **Model Selection** - Choose the right model for your use case (speed vs. capabilities)
- **Multimodal Optimization** - Optimize image/audio file sizes for better performance

This integration makes it easy to leverage Gemini's advanced capabilities while maintaining compatibility with existing OpenAI-based codebases.