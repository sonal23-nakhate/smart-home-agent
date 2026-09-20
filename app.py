import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

# Initialize Groq client with environment variable check
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

@app.route("/")
def home():
    return render_template("index.html", states=device_states)

@app.route("/command", methods=["POST"])
def process_command():
    data = request.get_json()
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"message": "I didn't catch that.", "states": device_states})

    # Validate client initialization
    if not client:
        print("Error: GROQ_API_KEY is not configured on Render.")
        return jsonify({
            "message": "API Key missing in Render settings. Please configure GROQ_API_KEY.",
            "states": device_states
        }), 500

    try:
       # Call Groq LLM API
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Current device states: {json.dumps(device_states)}. Command: '{command}'"}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        # Apply device state changes
        for device in ["light", "fan", "ac"]:
            if llm_response.get(device) in ["ON", "OFF"]:
                device_states[device] = llm_response[device]

        response_msg = llm_response.get("response_message", "Updated device states.")
        return jsonify({"message": response_msg, "states": device_states})

    except Exception as e:
        print("LLM Execution Error:", str(e))
        return jsonify({
            "message": f"Error processing command via AI engine: {str(e)}",
            "states": device_states
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)