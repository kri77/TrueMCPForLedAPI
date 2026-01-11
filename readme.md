# MCP LED Controller

This project implements a **Model Context Protocol (MCP)** server to control an Arduino-based LED system via MCP tools.
It allows any MCP-compatible client (Claude Desktop, Claude Code, or other MCP clients) to directly control LEDs through standardized tools like `turn_on_led`, `set_mood`, and `get_led_status`.

---

## Features

- True MCP server compatible with any MCP client
- Works with Claude Desktop, Claude Code, and other MCP-compatible applications
- Communicates with an Arduino LED controller API (`/setLedStatus`, `/status`)
- Exposes 5 MCP tools for LED control
- Supports mood-based LED patterns (calm, alert, focus, happy, etc.)
- Standard MCP protocol over stdio for universal compatibility

---

## MCP Tools Available

| Tool             | Description                                    | Parameters                    |
|------------------|------------------------------------------------|-------------------------------|
| turn_on_led      | Turn on a specific LED by color                | `color: "red"/"yellow"/"green"/"blue"` |
| turn_off_leds    | Turn off all LEDs                              | none                          |
| set_led_pattern  | Set a custom 4-digit binary pattern            | `pattern: "1010"`             |
| set_mood         | Set LEDs based on predefined mood              | `mood: "calm"/"alert"/"happy"/etc` |
| get_led_status   | Get the current status of all LEDs             | none                          |

---

## Available Moods

The `set_mood` tool supports these moods:
- **Energy levels**: calm, alert, focus, idle, energetic, relaxed, sleepy
- **Emotional states**: happy, excited, creative, warning, caution
- **Work modes**: busy, thinking, success, error
- **Special**: party, night, sunrise, sunset

---

## Requirements

- Python 3.10+
- MCP Python SDK
- Requests library

Install via:

```bash
pip install -r requirements.txt
```

---

## Installation

### Prerequisites

1. **Install Python dependencies**:
   ```bash
   cd E:\prosjekter\ClaudeCode\ClaudeMCPForLedAPi
   pip install -r requirements.txt
   ```

2. **Ensure your Arduino LED API is running** on `localhost:5000`

---

## Integration with MCP Clients

This MCP server can be integrated with various MCP-compatible applications. Below are configuration instructions for different clients.

### Claude Desktop

Claude Desktop has native MCP support and is the primary desktop application for Claude AI.

**Configuration File Location**:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Configuration**:
```json
{
  "mcpServers": {
    "led-controller": {
      "command": "python",
      "args": [
        "/absolute/path/to/MCPForLedAPI.py"
      ]
    }
  }
}
```

**Windows Example**:
```json
{
  "mcpServers": {
    "led-controller": {
      "command": "python",
      "args": [
        "E:\\..\\MCPForLedAPI.py"
      ]
    }
  }
}
```

**Steps**:
1. Edit the configuration file
2. Add the LED controller configuration with the absolute path to `MCPForLedAPI.py`
3. Restart Claude Desktop
4. Start a new conversation
5. Verify by asking: "What MCP tools do you have available?"

---

### Claude Code (CLI)

Claude Code is the command-line interface for Claude with MCP support.

**Configuration File Location**:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS/Linux**: `~/.config/claude-code/config.json`

**Configuration** (same as Claude Desktop):
```json
{
  "mcpServers": {
    "led-controller": {
      "command": "python",
      "args": [
        "/absolute/path/to/MCPForLedAPI.py"
      ]
    }
  }
}
```

**Steps**:
1. Edit the configuration file
2. Add the LED controller configuration
3. Restart Claude Code
4. Start a new conversation
5. Test with: "Turn on the green LED"

---

### Other MCP Clients

The MCP protocol is an open standard. Any application that supports MCP can use this server.

**Generic Integration Steps**:

1. **Identify the MCP configuration method** for your client (usually a JSON config file)

2. **Add the server configuration**:
   ```json
   {
     "led-controller": {
       "command": "python",
       "args": ["/absolute/path/to/MCPForLedAPI.py"]
     }
   }
   ```

3. **Ensure the client can**:
   - Execute Python commands
   - Communicate via stdio (standard input/output)
   - Parse MCP protocol messages

4. **Test the integration** by checking if the 5 tools are available:
   - `turn_on_led`
   - `turn_off_leds`
   - `set_led_pattern`
   - `set_mood`
   - `get_led_status`

---

### Building Your Own MCP Client

You can create a custom client using MCP SDKs:

**MCP Client SDKs**:
- **TypeScript/JavaScript**: `@modelcontextprotocol/sdk`
- **Python**: `mcp`

**Example Python Client**:
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["E:\\..\\MCPForLedAPI.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")

            # Call a tool
            result = await session.call_tool("turn_on_led", {"color": "green"})
            print(f"Result: {result}")

asyncio.run(main())
```

---

## Usage Examples

Once configured with any MCP client, you can control your LEDs through natural language:

- "Turn on the green LED"
- "Set the mood to calm"
- "What's the current LED status?"
- "Turn off all LEDs"
- "Set LED pattern to 1010"
- "Make the LEDs show a happy mood"

Or programmatically through tool calls:

```python
# turn_on_led tool
{"color": "red"}

# set_mood tool
{"mood": "happy"}

# set_led_pattern tool
{"pattern": "1010"}

# turn_off_leds tool
{}

# get_led_status tool
{}
```

---

## Architecture Overview

```
[ Any MCP Client ]
  (Claude Desktop, Claude Code, Custom Client, etc.)
        ↓
     MCP Protocol (stdio)
        ↓
  MCP LED Controller (Python)
        ↓
Arduino LED API (Flask at localhost:5000)
        ↓
      Arduino Nano (via USB)
```

The MCP server acts as a bridge between AI assistants and your hardware, translating high-level intent commands into low-level LED control signals.

---

## File Overview

- `MCPForLedAPI.py`: MCP server implementation with LED control tools
- `requirements.txt`: Python dependencies
- `mcp-config-example.json`: Example configuration for Claude Code
- `README.md`: Project overview and usage

---

## Protocol Details

### Communication

- **Protocol**: Model Context Protocol (MCP)
- **Transport**: stdio (standard input/output)
- **Message Format**: JSON-RPC 2.0
- **Server Name**: `led-controller`

### Tool Specifications

All tools follow the MCP tool schema:

```typescript
interface Tool {
  name: string;
  description: string;
  inputSchema: JSONSchema;
}
```

Each tool returns a `TextContent` response with the operation result.

---

## Troubleshooting

### MCP Server Not Showing Up

1. **Check configuration path**: Ensure the path to `MCPForLedAPI.py` is absolute and correct
2. **Verify Python installation**: Run `python --version` (should be 3.10+)
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Restart the MCP client** completely
5. **Start a new conversation** (MCP servers load at conversation start)
6. **Check logs**: Look for MCP-related errors in your client's logs

### Tool Calls Failing

1. **Arduino LED API not running**: Ensure the Flask API is running on `localhost:5000`
2. **Test the API directly**:
   ```bash
   curl http://localhost:5000/status
   curl -X POST http://localhost:5000/setLedStatus -H "Content-Type: application/json" -d '{"pattern":"0010"}'
   ```
3. **Check firewall**: Ensure localhost connections are allowed
4. **Verify Arduino connection**: Check that the Arduino is connected via USB

### Connection Issues

1. Ensure your Arduino LED API is running on `localhost:5000`
2. Test the LED API endpoints:
   - Status: `GET http://localhost:5000/status`
   - Set pattern: `POST http://localhost:5000/setLedStatus`
3. Check that the Arduino is connected and recognized by the OS
4. Verify firewall settings allow local connections

### Python Environment Issues

1. **Wrong Python version**: Use Python 3.10 or higher
2. **Missing dependencies**: Run `pip install -r requirements.txt`
3. **Virtual environment**: Consider using venv or conda for isolated dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## Development

### Extending the Server

You can add new tools by modifying `MCPForLedAPI.py`:

1. **Add a new tool definition** in the `list_tools()` function
2. **Implement the tool handler** in the `call_tool()` function
3. **Test the new tool** with your MCP client

Example adding a `blink_led` tool:

```python
# In list_tools():
Tool(
    name="blink_led",
    description="Blink an LED with a specific pattern",
    inputSchema={
        "type": "object",
        "properties": {
            "color": {"type": "string", "enum": ["red", "yellow", "green", "blue"]},
            "times": {"type": "number", "description": "Number of blinks"}
        },
        "required": ["color", "times"]
    }
)

# In call_tool():
elif name == "blink_led":
    color = arguments["color"]
    times = arguments["times"]
    # Implement blinking logic
    return [TextContent(type="text", text=f"Blinked {color} LED {times} times")]
```

### Testing

Test the MCP server directly:

```bash
# Run the server
python MCPForLedAPI.py

# The server will wait for stdio input
# You can test by sending MCP protocol messages
```

Or use the example Python client provided in the "Building Your Own MCP Client" section.

---

## Resources

- **MCP Documentation**: https://modelcontextprotocol.io
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **Claude Desktop**: https://claude.ai/desktop
- **MCP Specification**: https://spec.modelcontextprotocol.io

---

## Contributing

Contributions are welcome! Feel free to:
- Add new LED control patterns
- Improve error handling
- Add new tools
- Enhance documentation
- Support additional hardware

---

## License

MIT License
