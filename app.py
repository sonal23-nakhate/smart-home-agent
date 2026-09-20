from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

device_states = {
    "light": "OFF",
    "fan": "OFF",
    "ac": "OFF"
}

@app.route("/")
def home():
    return render_template("index.html", states=device_states)

@app.route("/command", methods=["POST"])
def process_command():
    data = request.get_json()
    command = data.get("command", "").lower()
    
    response_msg = "Command not recognized."
    
    if "turn on the light" in command or "light on" in command:
        device_states["light"] = "ON"
        response_msg = "Turning on the light."
    elif "turn off the light" in command or "light off" in command:
        device_states["light"] = "OFF"
        response_msg = "Turning off the light."
    elif "turn on the fan" in command or "fan on" in command:
        device_states["fan"] = "ON"
        response_msg = "Turning on the fan."
    elif "turn off the fan" in command or "fan off" in command:
        device_states["fan"] = "OFF"
        response_msg = "Turning off the fan."
    elif "turn on the ac" in command or "ac on" in command:
        device_states["ac"] = "ON"
        response_msg = "Turning on the AC."
    elif "turn off the ac" in command or "ac off" in command:
        device_states["ac"] = "OFF"
        response_msg = "Turning off the AC."

    return jsonify({"message": response_msg, "states": device_states})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)