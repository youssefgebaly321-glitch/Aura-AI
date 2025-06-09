# Llama 4 Vision Models Guide

## Model Overview

### meta-llama/llama-4-maverick-17b-128e-instruct

**Description:** A powerful multimodal model capable of processing both text and image inputs that supports multilingual, multi-turn conversations, tool use, and JSON mode.

**Key Specifications:**
- **Context Window:** 128K tokens
- **Status:** Preview Model (for experimentation)
- **Capabilities:** Text and image processing, multilingual support, tool use, JSON mode

## Technical Limitations

### Image Processing Constraints

**Image Size Limits:**
- Maximum image URL size: 20MB (returns 400 error if exceeded)
- Maximum base64 encoded image size: 4MB (returns 413 error if exceeded)

**Image Resolution:**
- Maximum resolution: 33 megapixels (33,177,600 total pixels) per image

**Images per Request:**
- Process multiple images in a single request
- Recommended maximum: 5 images for optimal quality and accuracy

## Getting Started with Vision

### Using GroqCloud Console
1. Select Llama 4 Scout or Llama 4 Maverick as the model
2. Upload your image directly in the playground

### API Integration
Use the chat.completions endpoint with these model options:
- `meta-llama/llama-4-scout-17b-16e-instruct`
- `meta-llama/llama-4-maverick-17b-128e-instruct`

## Implementation Examples

### Processing Images from URLs

```bash
curl "https://api.groq.com/openai/v1/chat/completions" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GROQ_API_KEY}" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What'\''s in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://upload.wikimedia.org/wikipedia/commons/f/f2/LPU-v1-die.jpg"
            }
          }
        ]
      }
    ],
    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "temperature": 1,
    "max_completion_tokens": 1024,
    "top_p": 1,
    "stream": false,
    "stop": null
  }'
```

### Processing Local Images (Base64 Encoding)

```python
from groq import Groq
import base64
import os

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Initialize client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Encode your image
image_path = "sf.jpg"
base64_image = encode_image(image_path)

# Make API call
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }
    ],
    model="meta-llama/llama-4-scout-17b-16e-instruct",
)

print(chat_completion.choices[0].message.content)
```

## Advanced Features

### Tool Use with Images

The models support tool integration for enhanced functionality. Here's an example of weather tool integration:

```bash
curl https://api.groq.com/openai/v1/chat/completions -s \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -d '{
    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text", 
            "text": "What'\''s the weather like in this state?"
          }, 
          {
            "type": "image_url", 
            "image_url": { 
              "url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
            }
          }
        ]
      }
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_current_weather",
          "description": "Get the current weather in a given location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA"
              },
              "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"]
              }
            },
            "required": ["location"]
          }
        }
      }
    ],
    "tool_choice": "auto"
  }'
```

**Expected Output:**
```json
[
  {
    "id": "call_q0wg",
    "function": {
      "arguments": "{\"location\": \"New York, NY\",\"unit\": \"fahrenheit\"}",
      "name": "get_current_weather"
    },
    "type": "function"
  }
]
```

### JSON Mode with Images

Extract structured data from images using JSON mode:

```python
from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

completion = client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "List what you observe in this photo in JSON format."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/d/da/SF_From_Marin_Highlands3.jpg"
                    }
                }
            ]
        }
    ],
    temperature=1,
    max_completion_tokens=1024,
    top_p=1,
    stream=False,
    response_format={"type": "json_object"},
    stop=None,
)

print(completion.choices[0].message)
```

### Multi-turn Conversations

Engage in contextual conversations about images:

```python
from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

completion = client.chat.completions.create(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/d/da/SF_From_Marin_Highlands3.jpg"
                    }
                }
            ]
        },
        {
            "role": "user",
            "content": "Tell me more about the area."
        }
    ],
    temperature=1,
    max_completion_tokens=1024,
    top_p=1,
    stream=False,
    stop=None,
)

print(completion.choices[0].message)
```

## Practical Applications

### Accessibility Solutions
- **Audio Descriptions:** Generate text descriptions of images that can be converted to audio for visually impaired users
- **Screen Reader Enhancement:** Provide detailed context for images in web applications

### E-commerce Integration
- **Product Description Generation:** Automatically create detailed product descriptions from product images
- **Inventory Analysis:** Analyze product images for cataloging and categorization

### Multilingual Applications
- **Global Content Creation:** Generate image descriptions in multiple languages
- **Cross-cultural Communication:** Bridge language barriers through visual content analysis

### Interactive Applications
- **Visual Conversations:** Build chatbots that can discuss and analyze images
- **Educational Tools:** Create interactive learning experiences with visual content

## Best Practices

1. **Image Quality:** Use high-resolution images within the 33MP limit for best results
2. **Batch Processing:** Process multiple related images together for context
3. **Clear Prompts:** Provide specific instructions about what information you need from images
4. **Error Handling:** Implement proper error handling for size and resolution limits
5. **Performance Optimization:** Use appropriate temperature and token limits for your use case

## Getting Started

The Llama 4 vision models offer powerful capabilities for multimodal AI applications. With support for tool use, JSON mode, and multi-turn conversations, these models enable developers to create sophisticated applications that understand and interact with visual content at high speed and low latency through Groq's infrastructure.