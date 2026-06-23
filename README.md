# ETH/USDT Technical Analysis Signal Bot

Bot phân tích kỹ thuật ETH/USDT từ Binance và gửi cảnh báo Buy/Sell qua Telegram khi điểm tín hiệu đạt ngưỡng.

## Cấu trúc repo

```
eth_signal_bot/
├── core/
│   ├── config.py        # Biến môi trường
│   └── scheduler.py     # Vòng lặp chính
├── exchanges/
│   └── binance.py       # Gọi Binance API
├── indicators/
│   ├── technicals.py    # RSI, EMA, MA, MACD
│   └── signals.py       # Logic chấm điểm tín hiệu
├── notifiers/
│   └── telegram.py      # Gửi tin nhắn Telegram
└── health/
    └── server.py        # HTTP health-check
main.py                  # Entry point
Procfile                 # Railway process
requirements.txt
runtime.txt
.env.example
```

## Chạy local

1. Copy `.env.example` thành `.env` và điền `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
2. Cài dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Chạy:
   ```bash
   python main.py
   ```

## Deploy lên Railway

1. Push repo lên GitHub.
2. Trong Railway: **New Project → Deploy from GitHub repo**.
3. Thêm **Variables** từ `.env.example` (bỏ qua `PORT` nếu Railway tự inject).
4. Railway sẽ dùng `Procfile` chạy `python main.py`.
5. Health-check chạy trên cổng `PORT` (mặc định 8080) để giữ container alive.

## Tùy chỉnh

- Đổi khung thờ gian: `TF_1H`, `TF_4H`, `TF_1D`.
- Đổi ngưỡng: `BUY_THRESHOLD`, `SELL_THRESHOLD`.
- Đổi vùng hỗ trợ/kháng cự: `SUPPORT_ZONES`, `RESISTANCE_ZONES`.
