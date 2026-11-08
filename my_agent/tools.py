
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g., San Francisco, CA"
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
]


def get_weather(location: str, unit: str = "celsius"):
    value = "70" if unit == "fahrenheit" else "21"
    return f"The weather in {location} is {value} degrees {unit}"


# Dispatch table: tool name -> the Python function to run.
# The names here MUST match the "name" fields declared in TOOLS above,
# since that's the name the model will send back when it wants to call one.
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
}
