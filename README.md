# ETH/USDT Technical Analysis Signal Bot

Bot phân tích kỹ thuật ETH/USDT từ Binance và gửi cảnh báo Buy/Sell qua Telegram khi điểm tín hiệu đạt ngưỡng.
Bot cũng có thể kiểm tra định kỳ tỷ trọng market cap USDT từ CoinGecko và gửi Telegram khi giá trị đi vào vùng cấu hình.

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
│   ├── zones.py         # Support/Resistance động, Fibonacci, POC, volume walls
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
   python3 main.py
   ```
4. Mở dashboard:
   ```text
   http://127.0.0.1:8080/
   ```

## Dashboard index

- `/` hiển thị dashboard read-only để nắm nhanh giá ETH, hướng Buy/Sell, score tổng hợp, vùng hỗ trợ/kháng cự động, Fibonacci, POC, volume walls và phân tích theo khung thời gian.
- `/api/snapshot` trả JSON snapshot cho dashboard. Endpoint này dùng cache theo `CHECK_INTERVAL`; thêm `?refresh=1` để yêu cầu làm mới thủ công nhưng vẫn có cooldown ngắn.
- `/health` vẫn trả `OK` dạng plain text cho Railway / uptime monitor.
- Dashboard không gửi Telegram và không hiển thị token/chat id.
- Vùng giao dịch không còn hardcode. Bot tự tính từ pivot high/low, EMA/MA, Fibonacci swing high/low và Volume Profile trên dữ liệu nến mới.

## Cảnh báo USDT market cap percentage

- Bot gọi `COINGECKO_GLOBAL_URL` mặc định `https://api.coingecko.com/api/v3/global`.
- Field được kiểm tra là `data.market_cap_percentage.usdt`.
- Mặc định cứ `USDT_DOMINANCE_CHECK_INTERVAL=600` giây kiểm tra một lần.
- Nếu giá trị đi vào vùng inclusive `USDT_DOMINANCE_MIN=8.4` đến `USDT_DOMINANCE_MAX=8.5`, bot gửi một tin Telegram.
- Bot chỉ gửi khi giá trị chuyển từ ngoài vùng vào trong vùng, không spam mỗi 10 phút khi giá trị vẫn nằm trong vùng.

## Deploy lên Railway

1. Push repo lên GitHub.
2. Trong Railway: **New Project → Deploy from GitHub repo**.
3. Thêm **Variables** từ `.env.example` (bỏ qua `PORT` nếu Railway tự inject).
4. Railway sẽ dùng `Procfile` chạy `python main.py`.
5. Health-check chạy trên cổng `PORT` (mặc định 8080) để giữ container alive.

## Tùy chỉnh

- Đổi khung thờ gian: `TF_1H`, `TF_4H`, `TF_1D`.
- Đổi ngưỡng: `BUY_THRESHOLD`, `SELL_THRESHOLD`.
- Đổi cảnh báo USDT: `USDT_DOMINANCE_MIN`, `USDT_DOMINANCE_MAX`, `USDT_DOMINANCE_CHECK_INTERVAL`.
- Vùng hỗ trợ/kháng cự, Fibonacci, POC và volume walls được tính tự động theo thị trường.
