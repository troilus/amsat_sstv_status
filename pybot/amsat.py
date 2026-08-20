# -*- coding: utf-8 -*-
"""Thin client for the AMSAT Satellite Status API.

- get_catalog(): list of satellites, with JSON-file caching.
- get_statuses(): canonical report values.
- submit_report(): POST a new report.
"""

import json
import urllib.error
import urllib.request

USER_AGENT = "amsat-status-pybot/1.0"

DEFAULT_STATUSES = [
    {"value": "Heard", "label": "Satellite active"},
    {"value": "Telemetry Only", "label": "Telemetry or beacon only"},
    {"value": "Not Heard", "label": "No signal"},
    {"value": "Crew Active", "label": "ISS crew voice active"},
]


def _http_get_json(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_post_json(url, payload, timeout=20):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def get_catalog(store, api_base, ttl):
    """Return the satellite catalog, using the store as a TTL cache."""
    cached = store.get_catalog()
    if cached is not None:
        return cached
    data = _http_get_json(f"{api_base}/catalog.php?include_stats=true")
    sats = data.get("data") or []
    if sats:
        store.set_catalog(sats, ttl)
    return sats


def get_statuses(api_base):
    try:
        data = _http_get_json(f"{api_base}/statuses.php")
        statuses = data.get("data") or []
        if statuses:
            return statuses
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError):
        pass
    return DEFAULT_STATUSES


def submit_report(api_base, payload):
    """Submit a report. Returns (ok, message)."""
    try:
        status, data = _http_post_json(f"{api_base}/reports.php", payload)
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
            msg = body.get("error", {}).get("message") or f"HTTP {e.code}"
        except (ValueError, UnicodeDecodeError):
            msg = f"HTTP {e.code}"
        return False, msg
    except urllib.error.URLError as e:
        return False, str(e.reason)
    if status < 300:
        return True, None
    msg = data.get("error", {}).get("message") or f"HTTP {status}"
    return False, msg