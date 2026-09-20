import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

# Initialize Groq client securely
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

device_states = {
    "light": "OFF",
    "fan": "OFF",
    "ac": "OFF"
}

SYSTEM_PROMPT = """
You are an AI Smart Home Agent. Parse user voice commands and extract device control intents.
The available devices are: "light", "fan", "ac".
Actions allowed: "ON", "OFF", or "NO_CHANGE".

Return ONLY a valid JSON object matching this exact structure:
{
  "light": "ON" | "OFF" | "NO_CHANGE",
  "fan": "ON" | "OFF" | "NO_CHANGE",
  "ac": "ON" | "OFF" | "NO_CHANGE",
  "response_message": "A short natural spoken response to confirm action to the user."
}
"""

def rule_based_fallback(command):
    """Fallback rule-based parser if API key fails or models are unavailable."""
    cmd = command.lower()
    actions = []

    if "light" in cmd:
        if "on" in cmd:
            device_states["light"] = "ON"
            actions.append("turned on the light")
        elif "off" in cmd:
            device_states["light"] = "OFF"
            actions.append("turned off the light")

    if "fan" in cmd:
        if "on" in cmd:
            device_states["fan"] = "ON"
            actions.append("turned on the fan")
        elif "off" in cmd:
            device_states["fan"] = "OFF"
            actions.append("turned off the fan")

    if "ac" in cmd or "air conditioner" in cmd:
        if "on" in cmd:
            device_states["ac"] = "ON"
            actions.append("turned on the AC")
        elif "off" in cmd:
            device_states["ac"] = "OFF"
            actions.append("turned off the AC")

    if actions:
        msg = f"Done! I've {', and '.join(actions)}."
    else:
        msg = "Command received, but no state changes were required."

    return jsonify({"message": msg, "states": device_states})


@app.route("/")
def home():
    return render_template("index.html", states=device_states)


@app.route("/command", methods=["POST"])
def process_command():
    data = request.get_json()
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"message": "I didn't catch that.", "states": device_states})

    if not client:
        print("GROQ_API_KEY missing or invalid. Using local rule-based intent parser.")
        return rule_based_fallback(command)

    # Active model targets
    models_to_try = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-20b"
    ]

    llm_response = None
    last_error = None

    for model_name in models_to_try:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Current device states: {json.dumps(device_states)}. Command: '{command}'"
                    }
                ],
                model=model_name,
                response_format={"type": "json_object"}
            )
            llm_response = json.loads(chat_completion.choices[0].message.content)
            print(f"Successfully processed command with model: {model_name}")
            break
        except Exception as err:
            last_error = err
            print(f"Model {model_name} failed: {err}")
            continue

    # If all Groq model attempts fail, execute rule-based fallback
    if not llm_response:
        print(f"All Groq models failed ({last_error}). Falling back to local parser.")
        return rule_based_fallback(command)

    # Update state matching LLM response
    for device in ["light", "fan", "ac"]:
        if llm_response.get(device) in ["ON", "OFF"]:
            device_states[device] = llm_response[device]

    response_msg = llm_response.get("response_message", "Updated device states.")
    return jsonify({"message": response_msg, "states": device_states})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)