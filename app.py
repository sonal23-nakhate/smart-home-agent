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
        # Array of active models to try in order
        models_to_try = [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "llama3-8b-8192",
            "mixtral-8x7b-32768"
        ]

        chat_completion = None
        last_error = None

        for model_name in models_to_try:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Current device states: {json.dumps(device_states)}. Command: '{command}'"}
                    ],
                    model=model_name,
                    response_format={"type": "json_object"}
                )
                print(f"Successfully used model: {model_name}")
                break
            except Exception as model_err:
                last_error = model_err
                continue

        if not chat_completion:
            raise Exception(f"All models failed. Last error: {str(last_error)}")

        llm_response = json.loads(chat_completion.choices[0].message.content)
        
        # Apply device state changes
        for device in ["light", "fan", "ac"]:
            if llm_response.get(device) in ["ON", "OFF"]:
                device_states[device] = llm_response[device]

        response_msg = llm_response.get("response_message", "Updated device states.")
        return jsonify({"message": response_msg, "states": device_states})
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