import os
# @todo swap for httpx for async ops.
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load .env for the server for testing.
HERE = Path(__file__).resolve().parent
load_dotenv(dotenv_path=HERE / ".env", override=False)

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

# Exit early if env vars are not set.
if not (JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN):
    raise RuntimeError("Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN")

mcp = FastMCP("jira")

def _auth() -> HTTPBasicAuth:
    # @todo Unsure how the API token access is affected by email.
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

def _get_with_debug(url: str):
    headers = {"Accept": "application/json"}
    try:
        resp = requests.request("GET", url, headers=headers, auth=_auth(), timeout=30)
        try:
            data = resp.json()
        except Exception:
            data = None
        return resp, data, None
    except Exception as e:
        return None, None, repr(e)

@mcp.tool()
async def jira_whoami() -> dict:
    attempts = []
    interesting_headers = {
        "x-atlassian-request-id", "x-arequestid", "x-request-id",
        "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset",
        "retry-after", "www-authenticate", "content-type", "server",
    }

    for ver in ("3", "2"):
        url = f"{JIRA_BASE_URL}/rest/api/{ver}/myself"
        resp, data, exc = _get_with_debug(url)
        att: Dict[str, Any] = {"url": url, "apiVersion": ver}

        if exc is not None:
            att.update({"ok": False, "exception": exc})
            attempts.append(att)
            continue

        hdr = {k.lower(): v for k, v in resp.headers.items()}
        hdr_filtered = {k: hdr.get(k) for k in interesting_headers if k in hdr}

        if resp.status_code < 400 and isinstance(data, dict) and ("accountId" in data or "name" in data or "self" in data):
            return {
                "ok": True,
                "apiVersion": ver,
                "accountId": data.get("accountId"),
                "name": data.get("displayName") or data.get("name"),
                "site": JIRA_BASE_URL,
                "authEmail": JIRA_EMAIL,
                "status": resp.status_code,
                "headers": hdr_filtered,
                "attempts": attempts
            }

        att.update(
            {
                "ok": False,
                "status": resp.status_code,
                "reason": getattr(resp, "reason", None),
                "headers": hdr_filtered,
                "jsonKeys": list(data.keys()) if isinstance(data, dict) else None,
                "errorMessages": (data or {}).get("errorMessages") if isinstance(data, dict) else None,
                "warningMessages": (data or {}).get("warningMessages") if isinstance(data, dict) else None,
                "bodyExcerpt": (resp.text or "")[:400] if not isinstance(data, dict) else None,
            }
        )
        attempts.append(att)

    return {
        "ok": False,
        "site": JIRA_BASE_URL,
        "authEmail": JIRA_EMAIL,
        "error": "myself endpoint failed on v3 and v2",
        "attempts": attempts,
        "hints": [
            "For 401 or 403 responses check your .env JIRA_EMAIL and JIRA_API_TOKEN values.",
            "For 400 responses check for API changes or missing values required in the request.",
            "For 500 responses Jira may be having issues.",
        ],
    }

@mcp.tool()
async def jira_search(jql: str) -> List[str]:
    results: List[str] = []
    page_size = 50
    params = {"jql": jql, "maxResults": page_size, "fields": "key"}

    url_new = f"{JIRA_BASE_URL}/rest/api/3/search/jql"

    headers = {"Accept": "application/json"}
    resp = requests.get(url_new, headers=headers, params=params, auth=_auth(), timeout=30)

    data = resp.json()
    results.extend([i["key"] for i in data.get("issues", [])])
    return results

if __name__ == "__main__":
    mcp.run()
