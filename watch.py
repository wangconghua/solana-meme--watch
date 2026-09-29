#!/usr/bin/env python3
"""
solana-meme-watch
A tiny Solana meme-coin price monitor with threshold alerts.

Polls a public price API every N seconds, compares the current price
against your entry (baseline) price, and prints alerts when the price
hits 2x / 3x (or any levels you set). Works for any Solana token mint.

Usage:
    pip install -r requirements.txt
    python watch.py --token <MINT> --baseline 0.00001234
    python watch.py --token <MINT> --baseline 0.00001234 --interval 300 --alerts 2.0 3.0 5.0 --once

Optional webhook alerts:
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
    # Prefer a pair quoted in SOL, fall back to the first pair.
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
    """Best-effort Telegram / Discord notifications via env vars."""
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


def main():
    ap = argparse.ArgumentParser(description="Solana meme-coin price monitor")
    ap.add_argument("--token", required=True, help="Token mint address (contract)")
    ap.add_argument("--baseline", required=True, type=float,
                    help="Your entry price in SOL per token (e.g. 0.00001234)")
    ap.add_argument("--interval", type=int, default=600,
                    help="Poll interval in seconds (default 600)")
    ap.add_argument("--alerts", type=float, nargs="+", default=[2.0, 3.0],
                    help="Alert at these multiples of baseline (default 2.0 3.0)")
    ap.add_argument("--once", action="store_true",
                    help="Check once and exit instead of looping")
    args = ap.parse_args()

    fired = set()
    while True:
        try:
            result = fetch_price(args.token)
        except (URLError, HTTPError, ValueError, KeyError) as exc:
            print("[warn] price fetch failed: {}".format(exc), flush=True)
            result = None
        if result:
            price_sol, price_usd, name = result
            if price_sol > 0:
                multiple = price_sol / args.baseline if args.baseline > 0 else 0
                print("[{}] {}  price={:.10f} SOL  (${:.8f})  x{:.2f}".format(
                    time.strftime("%Y-%m-%d %H:%M:%S"), name, price_sol, price_usd, multiple), flush=True)
                for level in args.alerts:
                    if multiple >= level and level not in fired:
                        fired.add(level)
                        msg = "[ALERT] {} hit x{:.1f} of baseline ({:.10f} SOL)".format(
                            name, level, price_sol)
                        print(msg, flush=True)
                        send_webhooks(msg)
            else:
                print("[{}] {}  no SOL-quoted pair, USD price=${:.8f}".format(
                    time.strftime("%Y-%m-%d %H:%M:%S"), name, price_usd), flush=True)
        else:
            print("[warn] no trading pairs found for {}".format(args.token), flush=True)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
