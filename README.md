# Example MPC Server - Jira Search

A very basic example of an MPC server that uses the Jira API to search for work
items.

## Setup

### Environment

I recommend using conda to create a virtual environment.

1. Clone the repository and set up the desired Python environment.
2. Install the requirements from `requirements.txt`.

### Environment variables

Copy the `.env.example` file to `.env` and fill in the required values.

### LM Studio

Add the following to your LM Studio MCP configuration:

```json
{
  "mcpServers": {
    ...
    "jira_test": {
      "command": "<path to Python interpreter>",
      "args": [
        "<path to mcp_jira.py>"
      ]
    }
  }
}
```

Example with conda:

```json
{
  "mcpServers": {
    ...
    "jira_test": {
      "command": "/Users/<username>/miniconda3/envs/<env name>/bin/python",
      "args": [
        "/Users/<username>/Developer/test-mcp-jira/mcp_jira.py"
      ]
    }
  }
}
```