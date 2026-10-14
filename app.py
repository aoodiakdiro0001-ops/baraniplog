#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baran IP Log — mini web server for connection analytics.
Designed & built by Baran Avisat (professional programmer).

LEGITIMATE USE ONLY: authorized penetration tests (engagement scope),
digital forensics on your own incidents, and your own link analytics.
Logging third parties without authorization may be illegal in your
jurisdiction (GDPR & equivalents). No credential harvesting, no fake
login pages — this tool only records standard HTTP metadata that every
web server (nginx/Apache) logs by default, then redirects the visitor.

Flow:  (1) HTTP request → (2) header extraction → (3) GeoIP lookup →
       (4) log to terminal + JSONL file → 302 redirect.
"""
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, redirect, request, Response

# ---------------------------------------------------------------- config
PORT = int(os.environ.get("IPLOG_PORT", "8090"))
REDIRECT_URL = os.environ.get("IPLOG_REDIRECT", "https://www.google.com")
LOG_FILE = os.environ.get("IPLOG_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs.jsonl"))
GEO_TIMEOUT = 8
ADMIN_KEY = os.environ.get("IPLOG_ADMIN_KEY") or secrets.token_urlsafe(16)
OWNER = {
    "designer": "Baran Avisat",
    "title": "Professional Programmer",
    "email": "baranavisat@gmail.com",
    "phone": "+90 531 326 37 22",
    "whatsapp": "https://wa.me/905313263722",
    "btc": "bc1q8dhtdrndxsl70e97t8grydfe6pjue37zrhzf6c",
    "usdt_trc20": "TLWdTjqqogkXNEXGiPWsGdjFP6ioycxeWW",
}
# ---------------------------------------------------------------- app
app = Flask(__name__)

UA_OS = [
    (r"iPhone|iPad|iPod", "iOS"), (r"Android", "Android"),
    (r"Windows NT 10", "Windows 10/11"), (r"Windows NT", "Windows"),
    (r"Mac OS X", "Mac OS X"), (r"Linux", "Linux"), (r"CrOS", "ChromeOS"),
]
UA_BR = [
    (r"Edg/", "Edge"), (r"OPR/|Opera", "Opera"), (r"Firefox/", "Firefox"),
    (r"Chrome/", "Chrome"), (r"Version/.*Safari", "Safari"),
]


def parse_ua(ua):
    ua = ua or ""
    os_name, br = "Unknown", "Unknown"
    for rx, name in UA_OS:
        if re.search(rx, ua):
            os_name = name
            break
    for rx, name in UA_BR:
        if re.search(rx, ua, re.I):
            br = name
            break
    mv = re.search(r"(?:Chrome|Firefox|Version|Edg)/([\d.]+)", ua)
    ver = mv.group(1) if mv else ""
    dev = "Mobile" if re.search(r"Mobile|Android|iPhone|iPad", ua) else "Desktop"
    return {"os": os_name, "browser": (br + " " + ver).strip(), "device": dev}


def client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    real = request.headers.get("X-Real-IP", "")
    if real:
        return real.strip()
    return (request.remote_addr or "").strip()


def is_private_ip(ip):
    return ip.startswith(("10.", "192.168.", "127.", "::1", "fc00:", "fe80:")) or ip == ""


def geo_lookup(ip):
    """ip-api.com free tier (no key). Returns {} on any failure."""
    if is_private_ip(ip):
        return {"note": "private/local IP — no GeoIP"}
    try:
        r = requests.get(
            "http://ip-api.com/json/" + ip,
            params={"fields": "status,country,city,isp,org,lat,lon,query"},
            timeout=GEO_TIMEOUT,
        )
        j = r.json()
        if j.get("status") == "success":
            return {
                "country": j.get("country", ""),
                "city": j.get("city", ""),
                "isp": j.get("isp", "") or j.get("org", ""),
                "lat": j.get("lat"), "lon": j.get("lon"),
            }
    except Exception as e:
        return {"note": "geo lookup failed: %s" % type(e).__name__}
    return {"note": "geo lookup: no data"}


def collect():
    ua = request.headers.get("User-Agent", "")
    ip = client_ip()
    entry = {
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "ip": ip,
        "ua": ua,
        "parsed": parse_ua(ua),
        "lang": request.headers.get("Accept-Language", ""),
        "referer": request.headers.get("Referer", "") or "Direct Link",
        "method": request.method,
        "path": request.path,
        "geo": geo_lookup(ip),
        "headers": {k: v for k, v in request.headers.items()},
    }
    return entry


def print_entry(e):
    g = e.get("geo", {})
    print("[+] New Connection Detected!", flush=True)
    print("-" * 40, flush=True)
    print("IP Address : %s" % e["ip"], flush=True)
    print("Country    : %s" % (g.get("country", "") or "-"), flush=True)
    print("City       : %s" % (g.get("city", "") or "-"), flush=True)
    print("ISP        : %s" % (g.get("isp", "") or "-"), flush=True)
    print("OS / Device: %s / %s (%s)" % (e["parsed"]["os"], e["parsed"]["browser"], e["parsed"]["device"]), flush=True)
    print("Language   : %s" % (e["lang"] or "-"), flush=True)
    print("Referer    : %s" % (e["referer"] or "-"), flush=True)
    print("Time       : %s" % e["time"], flush=True)
    print("-" * 40, flush=True)


def save_entry(e):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print("[+] Data saved to %s" % LOG_FILE, flush=True)
    except Exception as ex:
        print("[!] Save failed: %s" % ex, flush=True)


def handle():
    e = collect()
    print_entry(e)
    save_entry(e)
    print("[+] Redirecting target to %s" % REDIRECT_URL, flush=True)
    return redirect(REDIRECT_URL, code=302)


@app.route("/", methods=["GET", "POST", "HEAD"])
def index():
    return handle()


@app.route("/<path:_p>", methods=["GET", "POST", "HEAD"])
def catchall(_p):
    if _p in ("dashboard", "health", "favicon.ico"):
        return _dashboard_or_404(_p)
    return handle()


def _dashboard_or_404(_p):
    if _p == "health":
        return jsonify({"ok": True, "tool": "Baran IP Log", "designer": OWNER["designer"]})
    if _p == "dashboard":
        if request.args.get("key", "") != ADMIN_KEY:
            return Response("Forbidden — valid ?key required", status=403)
        rows = []
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            rows.append(json.loads(line))
        except Exception:
            pass
        rows = rows[-200:][::-1]
        cards = "".join(
            "<div style='border:1px solid #2a3557;border-radius:10px;padding:10px;margin:8px 0;font-size:13px'>"
            "<b>{ip}</b> · {c} {ci} · {isp}<br><small>{ua}<br>{lang} · ref: {ref} · {time}</small></div>".format(
                ip=r.get("ip", "?"), c=(r.get("geo", {}) or {}).get("country", "-"),
                ci=(r.get("geo", {}) or {}).get("city", ""),
                isp=(r.get("geo", {}) or {}).get("isp", ""),
                ua=(r.get("ua", "") or "")[:140], lang=r.get("lang", ""),
                ref=(r.get("referer", "") or "")[:80], time=r.get("time", ""))
            for r in rows)
        return ("<html><head><meta charset='utf-8'><title>Baran IP Log — dashboard</title></head>"
                "<body style='background:#0b0e17;color:#e3e9f5;font-family:monospace;max-width:900px;margin:auto;padding:20px'>"
                "<h2>🛰️ Baran IP Log — %d connections</h2>"
                "<p>Designed by <b>Baran Avisat</b> · %s · %s</p>%s"
                "<p><a style='color:#34d399' href='/dashboard?key=%s'>refresh</a></p>"
                "</body></html>" % (len(rows), OWNER["email"], OWNER["phone"], cards or "<p>No logs yet.</p>", ADMIN_KEY))
    return Response("Not found", status=404)


def main():
    print("=" * 46, flush=True)
    print("  🛰️  Baran IP Log  — by Baran Avisat", flush=True)
    print("  Listening : http://127.0.0.1:%d" % PORT, flush=True)
    print("  Redirect  : %s" % REDIRECT_URL, flush=True)
    print("  Log file  : %s" % LOG_FILE, flush=True)
    print("  Dashboard : http://127.0.0.1:%d/dashboard?key=%s" % (PORT, ADMIN_KEY), flush=True)
    print("  LEGAL: authorized testing only.", flush=True)
    print("=" * 46, flush=True)
    app.run(host="127.0.0.1", port=PORT, debug=False)


if __name__ == "__main__":
    main()
