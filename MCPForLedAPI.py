import asyncio
import requests
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

LED_API_BASE = "http://localhost:5000" #the url for the LED API used to communicate with the Arduino

# LED Pattern Translator, supports both simple and extended formats
# Simple format: "1010" (4-digit LED state)
# Extended format: "SSSS:OOOO:III" (state:order:interval)

def set_led_pattern(pattern: str):
    # Check if it's the extended format with blinking support
    if ":" in pattern:
        # Extended format: SSSS:OOOO:III
        parts = pattern.split(":")
        if len(parts) != 3:
            raise ValueError("Extended pattern format must be SSSS:OOOO:III")

        state, order, interval = parts

        # Validate state (4 digits: 0=off, 1=on steady, 2=blink)
        if len(state) != 4 or any(c not in "012" for c in state):
            raise ValueError("State must be 4 digits of 0s, 1s, or 2s (0=off, 1=on, 2=blink)")

        # Validate order (4 digits: 0=no sequence, 1-4=order position)
        if len(order) != 4 or any(c not in "01234" for c in order):
            raise ValueError("Order must be 4 digits of 0-4 (0=no sequence, 1-4=position)")

        # Validate interval (must be numeric)
        if not interval.isdigit():
            raise ValueError("Interval must be a numeric value in milliseconds")

        # Send extended format to Arduino
        res = requests.post(f"{LED_API_BASE}/setLedStatus", json={"pattern": pattern})
        return res.json()
    else:
        # Simple backward-compatible format: 4-digit binary
        if len(pattern) != 4 or any(c not in "01" for c in pattern):
            raise ValueError("Invalid LED pattern format. Must be 4 digits of 0s and 1s.")
        res = requests.post(f"{LED_API_BASE}/setLedStatus", json={"pattern": pattern})
        return res.json()

# Returns the current LED status from the API
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
        ),
        Tool(
            name="set_blink_pattern",
            description="Set LEDs with blinking support. Each LED can be off (0), on steady (1), or blinking (2). Optionally configure blink sequence order and interval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "led_states": {
                        "type": "string",
                        "description": "4-digit state pattern (0=off, 1=on steady, 2=blink). Example: '2020' for LEDs 1&3 blinking",
                        "pattern": "^[012]{4}$"
                    },
                    "blink_order": {
                        "type": "string",
                        "description": "4-digit blink sequence order (0=no sequence, 1-4=position). Example: '1234' for sequential. Default: '0000' (simultaneous)",
                        "pattern": "^[01234]{4}$",
                        "default": "0000"
                    },
                    "interval_ms": {
                        "type": "number",
                        "description": "Blink interval in milliseconds. Default: 500",
                        "default": 500,
                        "minimum": 50,
                        "maximum": 10000
                    }
                },
                "required": ["led_states"]
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

        elif name == "set_blink_pattern":
            led_states = arguments["led_states"]
            blink_order = arguments.get("blink_order", "0000")
            interval_ms = arguments.get("interval_ms", 500)

            # extended pattern format: SSSS:OOOO:III
            extended_pattern = f"{led_states}:{blink_order}:{interval_ms}"
            result = set_led_pattern(extended_pattern)

            # Build readable description
            state_desc = []
            for i, state in enumerate(led_states):
                led_colors = ["red", "yellow", "green", "blue"]
                if state == "1":
                    state_desc.append(f"{led_colors[i]} steady")
                elif state == "2":
                    order_pos = blink_order[i]
                    if order_pos == "0":
                        state_desc.append(f"{led_colors[i]} blinking")
                    else:
                        state_desc.append(f"{led_colors[i]} blinking (seq {order_pos})")

            desc_text = ", ".join(state_desc) if state_desc else "all LEDs off"
            return [TextContent(type="text", text=f"Set blink pattern: {desc_text} at {interval_ms}ms interval. Result: {result}")]

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


