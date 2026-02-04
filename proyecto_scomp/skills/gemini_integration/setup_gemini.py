import os

def setup_api_key():
    print("Google Gemini API Setup")
    print("-----------------------")
    api_key = input("Enter your Google Gemini API Key: ").strip()
    
    if not api_key:
        print("API Key cannot be empty.")
        return

    env_file = ".env"
    
    # Read existing content
    lines = []
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()
    
    # Check if key exists and replace, else append
    key_found = False
    new_lines = []
    for line in lines:
        if line.startswith("GOOGLE_API_KEY="):
            new_lines.append(f"GOOGLE_API_KEY={api_key}\n")
            key_found = True
        else:
            new_lines.append(line)
    
    if not key_found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"GOOGLE_API_KEY={api_key}\n")
    
    with open(env_file, "w") as f:
        f.writelines(new_lines)
    
    print(f"API Key saved to {env_file}")

if __name__ == "__main__":
    setup_api_key()
