from skills.gemini_integration.gemini_client import GeminiClient
import google.generativeai as genai

def test_connection():
    try:
        print("Testing Gemini Connection...")
        client = GeminiClient()
        response = client.generate_content("Say 'Hello from Gemini!'")
        print(f"Response: {response}")
        
        if "Hello" in response:
            print("SUCCESS: Connection verified.")
        else:
            print("WARNING: Unexpected response content.")
            print("Listing available models:")
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        print(f"- {m.name}")
            except Exception as e:
                print(f"Error listing models: {e}")

    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_connection()
