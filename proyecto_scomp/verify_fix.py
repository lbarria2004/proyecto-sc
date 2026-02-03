from config.settings import PROMPT_EXTRACCION

try:
    text = "THIS IS A TEST PDF CONTENT"
    prompt = PROMPT_EXTRACCION.replace("{TEXTO_PDF}", text)
    print("SUCCESS: Prompt replacement works correctly.")
    if "{TEXTO_PDF}" in prompt:
        print("FAILURE: Did not replace the placeholder.")
    else:
        print("SUCCESS: Placeholder replaced.")
except Exception as e:
    print(f"FAILURE: Exception occurred: {e}")
