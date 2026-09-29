#!/usr/bin/env python3
"""
watch_multi.py — monitor multiple Solana tokens from a JSON config file.

Config example (see tokens.example.json):
[
  {
    "token": "<MINT_ADDRESS>",
    "label": "mytoken",
    "baseline": 0.00001234,
    "alerts": [2.0, 3.0]
  }
]

Usage:
    cp tokens.example.json tokens.json   # then fill in your own tokens
    python watch_multi.py --config tokens.json
    python watch_multi.py --config tokens.json --interval 300 --once

Optional webhook alerts (same as watch.py):
    export TG_BOT_TOKEN=... TG_CHAT_ID=...
    export DISCORD_WEBHOOK_URL=...
"""
import argparse
import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

API = "https://api.dexscreener.com/latest/dex/tokens/{}"


def fetch_price(mint):
    """Return (price_in_sol, price_usd, pair_name) or None on failure."""
    req = Request(API.format(mint), headers={"User-Agent": "solana-meme-watch/1.0"})
    with urlopen(req, timeout=15) as resp:
        data = json.load(resp)
    pairs = data.get("pairs") or []
    if not pairs:
        return None
    pair = next((p for p in pairs if p.get("quoteToken", {}).get("symbol") == "SOL"), pairs[0])
    price_usd = float(pair.get("priceUsd") or 0)
    if pair.get("quoteToken", {}).get("symbol") == "SOL":
        price_sol = float(pair.get("priceNative") or 0)
    else:
        price_sol = 0.0
    name = "{} / {}".format(
        pair.get("baseToken", {}).get("symbol", "?"),
        pair.get("quoteToken", {}).get("symbol", "?"),
    )
    return price_sol, price_usd, name


def send_webhooks(text):
    tg_token = os.environ.get("TG_BOT_TOKEN")
    tg_chat = os.environ.get("TG_CHAT_ID")
    if tg_token and tg_chat:
        try:
            payload = json.dumps({"chat_id": tg_chat, "text": text}).encode()
            req = Request(
                "https://api.telegram.org/bot{}/sendMessage".format(tg_token),
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urlopen(req, timeout=10).read()
        except Exception:
            pass
    discord_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if discord_url:
        try:
            payload = json.dumps({"content": text}).encode()
            req = Request(
                discord_url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urlopen(req, timeout=10).read()
        except Exception:
            pass


def check_one(entry, fired):
    label = entry.get("label") or entry["token"][:8]
    try:
        result = fetch_price(entry["token"])
    except (URLError, HTTPError, ValueError, KeyError) as exc:
        print("[warn] {} price fetch failed: {}".format(label, exc), flush=True)
        return
    if not result:
        print("[warn] {}: no trading pairs found".format(label), flush=True)
        return
    price_sol, price_usd, name = result
    baseline = float(entry.get("baseline") or 0)
    if price_sol <= 0 or baseline <= 0:
        print("[{}] {} ({})  USD price=${:.8f}  (no SOL baseline)".format(
            time.strftime("%Y-%m-%d %H:%M:%S"), name, label, price_usd), flush=True)
        return
    multiple = price_sol / baseline
    print("[{}] {} ({})  price={:.10f} SOL  (${:.8f})  x{:.2f}".format(
        time.strftime("%Y-%m-%d %H:%M:%S"), name, label, price_sol, price_usd, multiple), flush=True)
    for level in entry.get("alerts", [2.0, 3.0]):
        key = (label, float(level))
        if multiple >= level and key not in fired:
            fired.add(key)
            msg = "[ALERT] {} ({}) hit x{:.1f} of baseline ({:.10f} SOL)".format(
                name, label, level, price_sol)
            print(msg, flush=True)
            send_webhooks(msg)


def main():
    ap = argparse.ArgumentParser(description="Monitor multiple Solana tokens")
    ap.add_argument("--config", required=True, help="Path to JSON config file")
    ap.add_argument("--interval", type=int, default=600,
                    help="Poll interval in seconds (default 600)")
    ap.add_argument("--once", action="store_true",
                    help="Check once and exit instead of looping")
    args = ap.parse_args()

    with open(args.config) as f:
        entries = json.load(f)
    if not isinstance(entries, list) or not entries:
        print("config must be a non-empty JSON list", file=sys.stderr)
        return 1

    fired = set()
    while True:
        for entry in entries:
            if "token" not in entry:
                print("[warn] config entry missing 'token', skipped", flush=True)
                continue
            check_one(entry, fired)
            time.sleep(2)  # be nice to the free API
        if args.once:
            break
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
