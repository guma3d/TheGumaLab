from flask import Flask, render_template, jsonify
import yfinance as yf
import redis
import json
from datetime import datetime

app = Flask(__name__)

# Redis 연결 (docker-compose의 서비스 이름 'redis' 사용)
try:
    cache = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
except Exception as e:
    print(f"Redis connection error: {e}")
    cache = None

# 관심 종목 리스트 (임시: 하드코딩, 추후 DB 연동)
WATCHLIST = [
    {"ticker": "AAPL", "name": "Apple Inc."},
    {"ticker": "005930.KS", "name": "Samsung Elec"},
    {"ticker": "NVDA", "name": "NVIDIA"}
]

# 시장 지표 리스트
INDICES = [
    {"ticker": "^KS11", "name": "KOSPI"},
    {"ticker": "^IXIC", "name": "NASDAQ"},
    {"ticker": "^GSPC", "name": "S&P 500"}
]

def fetch_stock_data(tickers):
    """
    yfinance를 활용하여 현재가와 등락률을 반환합니다.
    """
    result = []
    for item in tickers:
        ticker = item["ticker"]
        name = item["name"]
        
        # 캐시 확인 (만료 시간 설정 5분)
        cache_key = f"stock_data:{ticker}"
        if cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                result.append(json.loads(cached_data))
                continue
                
        try:
            stock = yf.Ticker(ticker)
            # 가장 최근의 1일치 데이터 가져오기
            hist = stock.history(period="2d")
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                
                # 등락률 계산
                change_percent = ((current_price - prev_close) / prev_close) * 100
                
                data = {
                    "ticker": ticker.replace(".KS", ""), # 한국 주식의 경우 UI 표시용으로 .KS 제거
                    "name": name,
                    "price": float(round(current_price, 2)),
                    "change": float(round(change_percent, 2)),
                    "is_up": bool(change_percent >= 0),
                    "currency": "₩" if ".KS" in ticker else "$"
                }
            else:
                data = {
                    "ticker": ticker.replace(".KS", ""),
                    "name": name,
                    "price": "N/A",
                    "change": 0.0,
                    "is_up": True,
                    "currency": ""
                }
                
            # 캐시에 저장 (300초 = 5분 동안 유지하여 호출 제한 방어)
            if cache:
                cache.setex(cache_key, 300, json.dumps(data))
                
            result.append(data)
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            result.append({
                "ticker": ticker.replace(".KS", ""),
                "name": name,
                "price": "Error",
                "change": 0.0,
                "is_up": True,
                "currency": ""
            })
            
    return result

@app.route("/")
def home():
    # Render the styled dashboard
    return render_template("index.html")

@app.route("/api/market-indices")
def api_market_indices():
    data = fetch_stock_data(INDICES)
    return jsonify(data)

@app.route("/api/watchlist")
def api_watchlist():
    data = fetch_stock_data(WATCHLIST)
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
