# DataPuppet

**An MCP Server for Robust Data Processing and Web Automation**

DataPuppet integrates the analytical engine of **DuckDB** (for processing massive datasets directly on disk) with **Playwright** (for invisible navigation and web scraping) into a unified Model Context Protocol (MCP) server. It enables AI agents in IDEs (such as VS Code, Cursor, Windsurf, and Antigravity) to utilize these capabilities natively as external tools.

---

## Architectural Principles and Rationale

AI agents embedded within IDEs face two critical constraints during data-intensive operations:

1. **Finite Context Windows:** Providing a 500,000-row CSV file directly into an AI chat interface immediately depletes token limits or causes memory exhaustion.
2. **Limited Native Browser Capabilities:** The native browser tools built into AI IDEs often rely on taking screenshots and performing OCR. This methodology is prohibitively slow (~15 seconds per page), inaccurate, and generally incapable of handling authenticated sessions.

DataPuppet overcomes these limitations:
- **Delegated SQL Execution:** The AI transmits a SQL query, and DataPuppet executes it directly against the target file on the local filesystem using DuckDB, returning only the aggregated results.
- **Headless Web Automation:** The AI requests a URL and a CSS selector, and DataPuppet utilizes an active Playwright Chromium instance to extract structured data precisely and rapidly, maintaining session cookies where necessary.

### Engineering Resilience: Subprocess Fault Isolation
Developing MCP servers that interface with native C++ libraries (e.g., DuckDB, Pandas) via standard streams (`stdio`) presents a unique architectural challenge. These libraries frequently attempt to read from `stdin` or write progress bars/warnings to `stdout` at the operating system level. In a `stdio`-based MCP environment, this behavior corrupts the JSON-RPC protocol, leading to irreversible silent hangs within the IDE.

**The Solution:**
DataPuppet implements a strict **Subprocess Fault Isolation** pattern. Every DuckDB query is packaged into a temporary script and executed in an isolated process with `stdin=subprocess.DEVNULL` and a strict 30-second timeout. 
- **Stdin Shielding:** C++ extensions cannot intercept the JSON-RPC packets.
- **Zero Silent Hangs:** Runaway queries are forcefully terminated after 30 seconds.
- **Fault Tolerance:** If a corrupted dataset causes a segmentation fault within DuckDB, only the child process crashes. The main MCP server and the IDE connection remain entirely stable.

---

## Available Tools

### `query_large_dataset`
Executes SQL queries against local data files (CSV, TSV, or Parquet) using DuckDB. The query is processed efficiently without loading the entire dataset into RAM.

**Parameters:**
- `filepath`: Absolute path to the data file.
- `sql_query`: Valid SQL query to execute.

### `navigate_and_extract_text`
Accesses a URL using a headless Chromium browser and extracts the internal text of the HTML element matching a specific CSS selector. Uses a Singleton pattern to maintain the browser instance warm for high-performance sequential requests.

**Parameters:**
- `url`: Full URL (e.g., "https://example.com").
- `selector`: Target CSS selector (defaults to "body").

---

## Installation and Deployment

### Recommended Approach (Using `uv`)
DataPuppet utilizes `uv`, the fast Python package and project manager, to ensure conflict-free and isolated execution.

1. Install `uv` (if not already installed):
   - **Windows:** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - **Mac/Linux:** `curl -LsSf https://astral.sh/uv/install.sh | sh`

2. Initialize the Playwright environment (required only once):
   ```bash
   uv run playwright install chromium
   ```

### IDE Configuration (mcp_config.json)

To register DataPuppet as a native tool within your AI IDE, append the following configuration to your `mcp_config.json` file. Ensure you replace `/absolute/path/to/Data-Puppet` with the actual path to this repository.

```json
{
  "mcpServers": {
    "DataPuppet": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/Data-Puppet",
        "run",
        "data-puppet"
      ]
    }
  }
}
```

---

## Development and Testing

The project is equipped with an automated test suite utilizing `pytest` to validate core functionalities, security barriers, and subprocess isolation.

To execute the test suite:
```bash
uv run pytest tests/
```

### Known Limitations
- **Anti-Bot Mechanisms:** Sites protected by sophisticated anti-bot systems (e.g., Cloudflare Turnstile, reCAPTCHA v3) may block the headless Playwright instance.
- **Supported Formats:** DuckDB integration currently supports CSV, TSV, and Parquet natively. Excel (`.xlsx`) support requires additional DuckDB extensions.

---

## License

MIT License.
