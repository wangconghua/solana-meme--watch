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
