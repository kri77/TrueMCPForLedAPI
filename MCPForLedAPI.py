import asyncio
import requests
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

LED_API_BASE = "http://localhost:5000"

# LED Pattern Translator
def set_led_pattern(pattern: str):
    if len(pattern) != 4 or any(c not in "01" for c in pattern):
        raise ValueError("Invalid LED pattern format. Must be 4 digits of 0s and 1s.")
    res = requests.post(f"{LED_API_BASE}/setLedStatus", json={"pattern": pattern})
    return res.json()

def get_led_status():
    res = requests.get(f"{LED_API_BASE}/status")
    return res.json()

# Mood patterns mapping
MOOD_PATTERNS = {
    "calm": "0001",       # blue
    "alert": "1111",      # all
    "focus": "0010",      # green
    "idle": "0000",       # off
    # Energy levels
    "energetic": "1100",  # red + yellow (warm, high energy)
    "relaxed": "0011",    # green + blue (cool, peaceful)
    "sleepy": "0001",     # blue (same as calm, or could be "0000")
    # Emotional states
    "happy": "0110",      # yellow + green (bright, positive)
    "excited": "1010",    # red + green (festive, christmas-y)
    "creative": "1001",   # red + blue (purple-ish, artistic)
    "warning": "1000",    # red only
    "caution": "0100",    # yellow only
    # Work modes
    "busy": "1110",       # all except blue (active but not overwhelming)
    "thinking": "0011",   # green + blue (cool, contemplative)
    "success": "0010",    # green (achievement, go)
    "error": "1000",      # red (problem)
    # Special
    "party": "1111",      # all (celebration)
    "night": "0001",      # blue (gentle night light)
    "sunrise": "1100",    # red + yellow (warm awakening)
    "sunset": "1010"      # red + green (transitional)
}

# Color patterns mapping
COLOR_PATTERNS = {
    "red": "1000",
    "yellow": "0100",
    "green": "0010",
    "blue": "0001"
}

# Create MCP server
app = Server("led-controller")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="turn_on_led",
            description="Turn on a specific LED by color. Available colors: red, yellow, green, blue",
            inputSchema={
                "type": "object",
                "properties": {
                    "color": {
                        "type": "string",
                        "description": "The color of the LED to turn on",
                        "enum": ["red", "yellow", "green", "blue"]
                    }
                },
                "required": ["color"]
            }
        ),
        Tool(
            name="turn_off_leds",
            description="Turn off all LEDs",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="set_led_pattern",
            description="Set a specific LED pattern using a 4-digit binary string (e.g., '1010' for red and green)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "4-digit binary pattern (e.g., '1010')",
                        "pattern": "^[01]{4}$"
                    }
                },
                "required": ["pattern"]
            }
        ),
        Tool(
            name="set_mood",
            description=f"Set LED pattern based on a mood. Available moods: {', '.join(MOOD_PATTERNS.keys())}",
            inputSchema={
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "The mood to set",
                        "enum": list(MOOD_PATTERNS.keys())
                    }
                },
                "required": ["mood"]
            }
        ),
        Tool(
            name="get_led_status",
            description="Get the current status of all LEDs",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "turn_on_led":
            color = arguments["color"].lower()
            pattern = COLOR_PATTERNS.get(color)
            if not pattern:
                raise ValueError(f"Unsupported color: {color}")
            result = set_led_pattern(pattern)
            return [TextContent(type="text", text=f"Turned on {color} LED. Result: {result}")]

        elif name == "turn_off_leds":
            result = set_led_pattern("0000")
            return [TextContent(type="text", text=f"Turned off all LEDs. Result: {result}")]

        elif name == "set_led_pattern":
            pattern = arguments["pattern"]
            result = set_led_pattern(pattern)
            return [TextContent(type="text", text=f"Set LED pattern to {pattern}. Result: {result}")]

        elif name == "set_mood":
            mood = arguments["mood"].lower()
            pattern = MOOD_PATTERNS.get(mood)
            if not pattern:
                raise ValueError(f"Unsupported mood: {mood}")
            result = set_led_pattern(pattern)
            return [TextContent(type="text", text=f"Set mood to '{mood}' with pattern {pattern}. Result: {result}")]

        elif name == "get_led_status":
            result = get_led_status()
            return [TextContent(type="text", text=f"LED Status: {result}")]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())


