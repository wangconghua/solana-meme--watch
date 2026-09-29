# solana-meme-watch

A tiny, dependency-free Solana meme-coin price monitor with threshold alerts.

一个轻量的 Solana meme 币价格监控小工具，无第三方依赖，支持涨幅提醒。

## Features

- Poll any Solana token mint via a free public price API (no API key needed)
- Compare against your entry (baseline) price and alert at 2x / 3x (configurable)
- Optional Telegram / Discord webhook notifications
- Zero dependencies — pure Python standard library

## Quick start

```bash
python watch.py --token <MINT_ADDRESS> --baseline 0.00001234
```

Check once and exit:

```bash
python watch.py --token <MINT_ADDRESS> --baseline 0.00001234 --once
```

Custom interval and alert levels:

```bash
python watch.py --token <MINT_ADDRESS> --baseline 0.00001234 --interval 300 --alerts 2.0 3.0 5.0
```

## Webhook alerts (optional)

```bash
export TG_BOT_TOKEN=your_bot_token TG_CHAT_ID=your_chat_id
# or
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
python watch.py --token <MINT_ADDRESS> --baseline 0.00001234
```

## Notes

- Prices come from a free public API; not financial advice. DYOR.
- Requires Python 3.8+.

## License

MIT

## Multi-token monitoring

Monitor several tokens at once with `watch_multi.py`:

```bash
cp tokens.example.json tokens.json   # fill in your own token mints + baselines
python watch_multi.py --config tokens.json
python watch_multi.py --config tokens.json --interval 300 --once
```

Each entry in the config has its own baseline price and alert levels:

```json
[
  {"token": "<MINT>", "label": "mytoken", "baseline": 0.00001234, "alerts": [2.0, 3.0]}
]
```

Note: `tokens.json` is your private config — never commit it. Only `tokens.example.json` (the template) belongs in the repo.
