"""HTTP health-check and read-only dashboard server."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from eth_signal_bot.core import config
from eth_signal_bot.core.analysis import analyze_market


_SNAPSHOT_CACHE = {
    "data": None,
    "created_at": 0.0,
    "error": None,
}
_CACHE_LOCK = threading.Lock()


INDEX_HTML = r"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ETH Signal Bot Index</title>
  <style>
    :root {
      --ink: #101419;
      --panel: #171d24;
      --panel-2: #1d252e;
      --line: #2a3441;
      --text: #e7edf3;
      --muted: #96a3b3;
      --buy: #14b8a6;
      --sell: #f43f5e;
      --watch: #d97706;
      --focus: #60a5fa;
      --shadow: 0 20px 60px rgba(0, 0, 0, .26);
    }
    * { box-sizing: border-box; }
    html { color-scheme: dark; }
    body {
      margin: 0;
      min-height: 100dvh;
      background:
        linear-gradient(180deg, rgba(96, 165, 250, .06), transparent 320px),
        var(--ink);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }
    button, .mono {
      font-family: "SFMono-Regular", "Cascadia Code", "Liberation Mono", Menlo, monospace;
      font-variant-numeric: tabular-nums;
    }
    .shell {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 40px;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 12px 0 20px;
    }
    .brand { display: grid; gap: 2px; }
    .brand strong {
      font-size: clamp(18px, 2vw, 24px);
      line-height: 1.1;
      letter-spacing: 0;
    }
    .brand span, .meta, .label, .note {
      color: var(--muted);
      font-size: 13px;
    }
    .actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      gap: 8px;
      padding: 7px 11px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      background: rgba(23, 29, 36, .72);
      white-space: nowrap;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--watch);
      box-shadow: 0 0 0 4px rgba(217, 119, 6, .14);
    }
    .dot.ok { background: var(--buy); box-shadow: 0 0 0 4px rgba(20, 184, 166, .14); }
    .refresh {
      min-height: 44px;
      border: 1px solid #385065;
      border-radius: 8px;
      padding: 0 14px;
      color: var(--text);
      background: #22303d;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, transform .18s ease;
    }
    .refresh:hover { background: #293847; border-color: #54708b; }
    .refresh:active { transform: translateY(1px); }
    .refresh:focus-visible, a:focus-visible {
      outline: 3px solid var(--focus);
      outline-offset: 3px;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.65fr) minmax(280px, .75fr);
      gap: 16px;
      align-items: stretch;
    }
    .panel {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(23, 29, 36, .92);
      box-shadow: var(--shadow);
    }
    .hero { padding: clamp(18px, 3vw, 30px); display: grid; gap: 24px; }
    .hero-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 20px;
    }
    .hero-head > * { min-width: 0; }
    .price {
      font-size: clamp(42px, 9vw, 92px);
      line-height: .95;
      letter-spacing: 0;
      margin: 0;
    }
    .change {
      display: inline-flex;
      margin-top: 12px;
      border-radius: 999px;
      padding: 5px 10px;
      font-weight: 700;
      background: rgba(150, 163, 179, .10);
    }
    .change.buy { color: var(--buy); background: rgba(20, 184, 166, .12); }
    .change.sell { color: var(--sell); background: rgba(244, 63, 94, .12); }
    .signal {
      min-width: 188px;
      border-left: 1px solid var(--line);
      padding-left: 20px;
      text-align: right;
    }
    .signal-title {
      display: block;
      font-size: clamp(24px, 4vw, 42px);
      font-weight: 800;
      line-height: 1.05;
      letter-spacing: 0;
    }
    .signal-title.buy { color: var(--buy); }
    .signal-title.sell { color: var(--sell); }
    .signal-title.neutral { color: var(--watch); }
    .rail-wrap { display: grid; gap: 10px; }
    .rail-labels {
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }
    .rail {
      position: relative;
      height: 16px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: linear-gradient(90deg, rgba(244,63,94,.85), rgba(217,119,6,.78), rgba(20,184,166,.85));
      overflow: hidden;
    }
    .marker {
      position: absolute;
      top: -6px;
      width: 4px;
      height: 28px;
      border-radius: 999px;
      background: #fff;
      box-shadow: 0 0 0 4px rgba(255,255,255,.20);
      transform: translateX(-50%);
      transition: left .3s ease;
    }
    .summary {
      margin: 0;
      max-width: 72ch;
      color: #c9d4df;
      font-size: 16px;
    }
    .side { padding: 18px; display: grid; align-content: start; gap: 16px; }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .metric, .zone {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: rgba(29, 37, 46, .72);
    }
    .metric strong, .zone strong { display: block; font-size: 18px; margin-top: 2px; }
    .zones { display: grid; gap: 10px; }
    .zone-list { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
    .zone-list.stack { display: grid; grid-template-columns: 1fr; }
    .tag {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 8px;
      color: var(--text);
      background: rgba(16, 20, 25, .5);
      font-size: 12px;
    }
    .section-title {
      margin: 22px 0 10px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
    }
    .section-title h2 { margin: 0; font-size: 18px; }
    .timeframes {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .tf { padding: 15px; display: grid; gap: 14px; box-shadow: none; }
    .tf-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
    .tf h3 { margin: 0; font-size: 20px; }
    .score { font-size: 22px; font-weight: 800; }
    .score.buy { color: var(--buy); }
    .score.sell { color: var(--sell); }
    .score.neutral { color: var(--watch); }
    .tf-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .stat {
      border-top: 1px solid var(--line);
      padding-top: 8px;
    }
    .stat strong { display: block; }
    .reasons {
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 7px;
      color: #c9d4df;
      font-size: 13px;
    }
    .disclaimer {
      margin-top: 18px;
      border: 1px solid rgba(217,119,6,.34);
      border-radius: 8px;
      padding: 12px 14px;
      color: #f5d6a4;
      background: rgba(217,119,6,.08);
    }
    .skeleton {
      position: relative;
      overflow: hidden;
      color: transparent !important;
      background: #202a35 !important;
      border-radius: 6px;
    }
    .skeleton::after {
      content: "";
      position: absolute;
      inset: 0;
      transform: translateX(-100%);
      background: linear-gradient(90deg, transparent, rgba(255,255,255,.08), transparent);
      animation: shimmer 1.2s infinite;
    }
    .error {
      display: none;
      margin-bottom: 14px;
      border: 1px solid rgba(244,63,94,.45);
      border-radius: 8px;
      padding: 12px 14px;
      color: #fecdd3;
      background: rgba(244,63,94,.10);
    }
    .error.show { display: block; }
    @keyframes shimmer { 100% { transform: translateX(100%); } }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        animation-duration: .01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: .01ms !important;
      }
    }
    @media (max-width: 820px) {
      .shell { width: min(100% - 24px, 680px); padding-top: 12px; }
      .topbar, .hero-head { align-items: stretch; flex-direction: column; }
      .actions { justify-content: flex-start; }
      .grid, .timeframes { grid-template-columns: 1fr; }
      .signal { border-left: 0; border-top: 1px solid var(--line); padding: 16px 0 0; text-align: left; }
      .metric-grid { grid-template-columns: 1fr; }
      .price { font-size: clamp(40px, 14vw, 54px); }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="brand">
        <strong>ETH Signal Bot Index</strong>
        <span>Bảng điều khiển tín hiệu kỹ thuật ETH/USDT</span>
      </div>
      <div class="actions">
        <span class="pill"><span id="status-dot" class="dot"></span><span id="status-text">Đang tải</span></span>
        <span id="updated-at" class="pill mono">--</span>
        <button id="refresh" class="refresh" type="button">Làm mới</button>
      </div>
    </header>

    <section id="error" class="error" role="alert"></section>

    <section class="grid" aria-label="Tổng quan thị trường">
      <div class="panel hero">
        <div class="hero-head">
          <div>
            <div class="label">Giá hiện tại</div>
            <h1 id="price" class="price mono skeleton">$0.00</h1>
            <span id="change" class="change mono">0.00%</span>
          </div>
          <div class="signal">
            <span class="label">Hướng tín hiệu</span>
            <span id="direction" class="signal-title neutral">Đang tải</span>
            <span id="confidence" class="meta">Độ tin cậy --</span>
          </div>
        </div>

        <div class="rail-wrap" aria-label="Thanh tín hiệu Sell Neutral Buy">
          <div class="rail-labels mono"><span>Sell</span><span>Neutral</span><span>Buy</span></div>
          <div class="rail"><span id="marker" class="marker" style="left: 50%"></span></div>
          <div id="score" class="meta mono">Score --</div>
        </div>

        <p id="summary" class="summary">Đang lấy dữ liệu thị trường và tổng hợp tín hiệu.</p>
      </div>

      <aside class="panel side" aria-label="Thông tin nhanh">
        <div class="metric-grid">
          <div class="metric"><span class="label">Cao 24h</span><strong id="high" class="mono">--</strong></div>
          <div class="metric"><span class="label">Thấp 24h</span><strong id="low" class="mono">--</strong></div>
          <div class="metric"><span class="label">Volume</span><strong id="volume" class="mono">--</strong></div>
          <div class="metric"><span class="label">POC 4h</span><strong id="poc" class="mono">--</strong></div>
        </div>
        <div class="zones">
          <div class="zone">
            <span class="label">Vùng hỗ trợ động</span>
            <div id="support-zones" class="zone-list"></div>
          </div>
          <div class="zone">
            <span class="label">Vùng kháng cự động</span>
            <div id="resistance-zones" class="zone-list"></div>
          </div>
          <div class="zone">
            <span class="label">Fibonacci swing H/L</span>
            <div id="fib-zones" class="zone-list stack"></div>
          </div>
          <div class="zone">
            <span class="label">Volume walls</span>
            <div id="volume-walls" class="zone-list"></div>
          </div>
          <div class="metric"><span class="label">Lần quét tiếp</span><strong id="next-refresh" class="mono">--</strong></div>
        </div>
      </aside>
    </section>

    <section class="section-title">
      <div>
        <h2>Phân tích theo khung</h2>
        <span class="note">RSI, MACD, EMA và lý do chính trên từng timeframe</span>
      </div>
    </section>
    <section id="timeframes" class="timeframes" aria-live="polite"></section>

    <p class="disclaimer">Tín hiệu chỉ dựa trên phân tích kỹ thuật từ bot, không phải lời khuyên tài chính.</p>
  </main>

  <script>
    const el = (id) => document.getElementById(id);
    const fmtMoney = (value, digits = 2) => new Intl.NumberFormat("en-US", {
      style: "currency", currency: "USD", maximumFractionDigits: digits
    }).format(Number(value || 0));
    const fmtNum = (value, digits = 0) => new Intl.NumberFormat("en-US", {
      maximumFractionDigits: digits
    }).format(Number(value || 0));
    const cls = (direction) => direction === "BUY" ? "buy" : direction === "SELL" ? "sell" : "neutral";

    function setLoading(isLoading) {
      el("refresh").disabled = isLoading;
      el("refresh").textContent = isLoading ? "Đang tải" : "Làm mới";
      el("price").classList.toggle("skeleton", isLoading && el("price").textContent === "$0.00");
    }

    function renderZones(id, zones) {
      el(id).innerHTML = (zones || []).map((zone) => `<span class="tag mono">${fmtMoney(zone, 0)}</span>`).join("");
    }

    function renderFibonacci(data) {
      const fib = data.fibonacci || {};
      const rows = ["0.382", "0.5", "0.618"].filter((key) => fib[key]).map((key) => {
        return `<span class="tag mono">Fib ${key}: ${fmtMoney(fib[key], 0)}</span>`;
      });
      if (data.swing_high && data.swing_low) {
        rows.unshift(`<span class="tag mono">H ${fmtMoney(data.swing_high, 0)} / L ${fmtMoney(data.swing_low, 0)}</span>`);
      }
      el("fib-zones").innerHTML = rows.join("") || `<span class="tag">Chưa có</span>`;
    }

    function renderVolumeWalls(walls) {
      el("volume-walls").innerHTML = (walls || []).slice(0, 3).map((wall) => {
        return `<span class="tag mono">${fmtMoney(wall.price, 0)}</span>`;
      }).join("") || `<span class="tag">Chưa có</span>`;
    }

    function renderTimeframes(rows) {
      el("timeframes").innerHTML = (rows || []).map((row) => {
        const directionClass = row.total_score > 0 ? "buy" : row.total_score < 0 ? "sell" : "neutral";
        const reasons = (row.signals || []).slice(0, 3).map((item) => `<li>${item}</li>`).join("");
        return `
          <article class="panel tf">
            <div class="tf-head">
              <h3 class="mono">${row.timeframe}</h3>
              <span class="score mono ${directionClass}">${row.total_score > 0 ? "+" : ""}${row.total_score.toFixed(0)}</span>
            </div>
            <div class="tf-stats">
              <div class="stat"><span class="label">RSI</span><strong class="mono">${row.rsi.toFixed(1)}</strong></div>
              <div class="stat"><span class="label">MACD Hist</span><strong class="mono">${row.macd_hist > 0 ? "+" : ""}${row.macd_hist.toFixed(2)}</strong></div>
              <div class="stat"><span class="label">EMA20</span><strong class="mono">${fmtMoney(row.ema20, 0)}</strong></div>
              <div class="stat"><span class="label">EMA50</span><strong class="mono">${fmtMoney(row.ema50, 0)}</strong></div>
            </div>
            <ul class="reasons">${reasons || "<li>Chưa có lý do nổi bật.</li>"}</ul>
          </article>
        `;
      }).join("");
    }

    function render(data) {
      const directionClass = cls(data.direction);
      const changeClass = Number(data.change_24h) >= 0 ? "buy" : "sell";
      const maxScore = Math.max(Number(data.buy_threshold || 3), Number(data.sell_threshold || 3), 1);
      const clamped = Math.max(-maxScore, Math.min(maxScore, Number(data.total_score || 0)));
      const markerLeft = ((clamped + maxScore) / (maxScore * 2)) * 100;

      el("status-dot").className = "dot ok";
      el("status-text").textContent = data.cache_age_seconds > data.check_interval ? "Dữ liệu cũ" : "Đang chạy";
      el("updated-at").textContent = `Cập nhật ${new Date(data.generated_at).toLocaleTimeString("vi-VN")}`;
      el("price").textContent = fmtMoney(data.price);
      el("price").classList.remove("skeleton");
      el("change").className = `change mono ${changeClass}`;
      el("change").textContent = `${Number(data.change_24h) >= 0 ? "+" : ""}${Number(data.change_24h).toFixed(2)}% 24h`;
      el("direction").className = `signal-title ${directionClass}`;
      el("direction").textContent = data.direction_label;
      el("confidence").textContent = `Độ tin cậy ${data.confidence_label}`;
      el("marker").style.left = `${markerLeft}%`;
      el("score").textContent = `Score ${Number(data.total_score) >= 0 ? "+" : ""}${Number(data.total_score).toFixed(1)} / ngưỡng mua +${data.buy_threshold}, bán -${data.sell_threshold}`;
      el("summary").textContent = data.summary;
      el("high").textContent = fmtMoney(data.high_24h);
      el("low").textContent = fmtMoney(data.low_24h);
      el("volume").textContent = fmtNum(data.volume, 0);
      el("poc").textContent = data.poc ? fmtMoney(data.poc, 0) : "--";
      el("next-refresh").textContent = `${Math.max(0, Number(data.next_refresh_seconds || 0)).toFixed(0)}s`;
      renderZones("support-zones", data.support_zones);
      renderZones("resistance-zones", data.resistance_zones);
      renderFibonacci(data);
      renderVolumeWalls(data.volume_walls);
      renderTimeframes(data.timeframes);
    }

    async function loadSnapshot(force = false) {
      setLoading(true);
      el("error").classList.remove("show");
      try {
        const response = await fetch(`/api/snapshot${force ? "?refresh=1" : ""}`, { cache: "no-store" });
        const payload = await response.json();
        if (!response.ok || payload.error) throw new Error(payload.error || "Không tải được dữ liệu.");
        render(payload);
      } catch (error) {
        el("status-dot").className = "dot";
        el("status-text").textContent = "Lỗi dữ liệu";
        el("error").textContent = `${error.message} Hãy thử lại sau ít phút.`;
        el("error").classList.add("show");
      } finally {
        setLoading(false);
      }
    }

    el("refresh").addEventListener("click", () => loadSnapshot(true));
    loadSnapshot(false);
    window.setInterval(() => loadSnapshot(false), 60000);
  </script>
</body>
</html>
"""


def _json_response(handler, payload, status=200):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _text_response(handler, body, status=200, content_type="text/plain; charset=utf-8"):
    encoded = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


def _snapshot_payload(force_refresh=False):
    now = time.time()
    ttl = max(config.CHECK_INTERVAL, 30)
    manual_refresh_cooldown = 30
    with _CACHE_LOCK:
        cached = _SNAPSHOT_CACHE["data"]
        cache_age = now - _SNAPSHOT_CACHE["created_at"] if cached else None
        if cached and (
            (not force_refresh and cache_age < ttl)
            or (force_refresh and cache_age < manual_refresh_cooldown)
        ):
            payload = dict(cached)
            payload["cache_age_seconds"] = int(cache_age)
            next_refresh = manual_refresh_cooldown if force_refresh else ttl
            payload["next_refresh_seconds"] = int(max(next_refresh - cache_age, 0))
            return payload, 200

        snapshot = analyze_market()
        if not snapshot:
            error_payload = {
                "error": "Không đủ dữ liệu thị trường để tạo snapshot.",
                "cache_age_seconds": int(cache_age or 0),
                "next_refresh_seconds": 30,
            }
            if cached:
                payload = dict(cached)
                payload.update(error_payload)
                return payload, 200
            return error_payload, 503

        _SNAPSHOT_CACHE["data"] = snapshot
        _SNAPSHOT_CACHE["created_at"] = time.time()
        _SNAPSHOT_CACHE["error"] = None
        payload = dict(snapshot)
        payload["cache_age_seconds"] = 0
        payload["next_refresh_seconds"] = ttl
        return payload, 200


class _HealthHandler(BaseHTTPRequestHandler):
    """Serve health checks, snapshot API, and dashboard index."""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            _text_response(self, "OK\n")
        elif parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        elif parsed.path == "/":
            _text_response(self, INDEX_HTML, content_type="text/html; charset=utf-8")
        elif parsed.path == "/api/snapshot":
            params = parse_qs(parsed.query)
            force_refresh = params.get("refresh", ["0"])[0] == "1"
            payload, status = _snapshot_payload(force_refresh=force_refresh)
            _json_response(self, payload, status=status)
        else:
            _text_response(self, "Not Found\n", status=404)

    def log_message(self, fmt, *args):
        # keep Railway logs clean
        pass


def start_health_server():
    """Start the health server in a background daemon thread."""
    server = ThreadingHTTPServer((config.HEALTH_HOST, config.HEALTH_PORT), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"   Health server listening on http://{config.HEALTH_HOST}:{config.HEALTH_PORT}")
