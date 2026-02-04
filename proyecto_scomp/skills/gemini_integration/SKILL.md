---
name: Gemini Integration
description: Interact with Google's Gemini API for content generation and chat.
---

# Gemini Integration Skill

This skill allows Antigravity and the user to interact with Google's Gemini models.

## usage

### Python Client

```python
from skills.gemini_integration.gemini_client import GeminiClient

client = GeminiClient()

# Generate text
response = client.generate_content("Explain quantum computing in 5 words.")
print(response)

# Chat
chat = client.start_chat()
response = client.send_message(chat, "Hello!")
print(response)
```

## Setup

1.  Obtain an API Key from Google AI Studio.
2.  Run `python skills/gemini_integration/setup_gemini.py` to save it to your `.env` file.
