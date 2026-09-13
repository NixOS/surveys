"""Import the 2026 survey into a freshly booted LimeSurvey and activate it.

Runs inside the preview VM, where only the standard library is available.
Shares its RPC plumbing with the import test next door; the two live in
different derivations and neither can import the other, so the handful of
lines below are duplicated deliberately.

Usage: import.py <base-url> <survey.txt> [browse-url]

``base-url`` is how the VM reaches itself; ``browse-url`` is how the person
running it reaches the VM, through the forwarded port. They differ, and
printing the first one sends the reader somewhere they cannot open.
"""

import base64
import json
import sys
import urllib.request


def rpc(url: str, method: str, *params):
    """One JSON-RPC call to LimeSurvey's RemoteControl 2 API.

    Failures arrive two ways: a JSON-RPC ``error`` field, or a result that is
    a one-key ``{"status": ...}`` dict. Both end the run.
    """
    body = json.dumps({"method": method, "params": list(params), "id": 1}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("error"):
        raise SystemExit(f"{method}: {payload['error']}")
    result = payload["result"]
    if isinstance(result, dict) and "status" in result and len(result) == 1:
        raise SystemExit(f"{method}: {result['status']}")
    return result


def main(base_url: str, tsv_path: str, browse_url: str | None = None) -> None:
    """Import, activate, and print where to find the survey."""
    url = f"{base_url}/index.php/admin/remotecontrol"
    key = rpc(url, "get_session_key", "admin", "password")
    try:
        with open(tsv_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        sid = rpc(url, "import_survey", key, data, "txt")
        # activate_survey creates the response table; without it the survey
        # renders but cannot be submitted, which is the half a reviewer needs.
        rpc(url, "activate_survey", key, sid)
        print(f"survey {sid} imported and activated")
        print(f"take it at {(browse_url or base_url).rstrip('/')}/index.php/{sid}")
    finally:
        rpc(url, "release_session_key", key)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if sys.argv[3:] else None)
