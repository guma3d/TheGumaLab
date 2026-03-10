from flask import Flask, render_template, jsonify
import yfinance as yf
import redis
import json
import sqlite3
import os
from google import genai
from datetime import datetime
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Redis 연결 (docker-compose의 서비스 이름 'redis' 사용)
try:
    cache = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
except Exception as e:
    print(f"Redis connection error: {e}")
    cache = None

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

DB_PATH = 'watchlist.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist (ticker TEXT PRIMARY KEY, name TEXT)''')
    # 기본 종목 셋팅
    c.execute('SELECT count(*) FROM watchlist')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO watchlist VALUES (?, ?)', [
            ('AAPL', 'Apple Inc.'),
            ('005930.KS', '삼성전자'),
            ('NVDA', 'NVIDIA')
        ])
    conn.commit()
    conn.close()

init_db()

def get_watchlist():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT ticker, name FROM watchlist')
    rows = c.fetchall()
    conn.close()
    return [{"ticker": r[0], "name": r[1]} for r in rows]

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
                    "raw_ticker": ticker,
                    "ticker": ticker.replace(".KS", ""), # 한국 주식의 경우 UI 표시용으로 .KS 제거
                    "name": name,
                    "price": float(round(current_price, 2)),
                    "change": float(round(change_percent, 2)),
                    "is_up": bool(change_percent >= 0),
                    "currency": "₩" if ".KS" in ticker else "$"
                }
            else:
                data = {
                    "raw_ticker": ticker,
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
                "raw_ticker": ticker,
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

@app.route("/api/watchlist", methods=["GET"])
def api_watchlist():
    watchlist = get_watchlist()
    data = fetch_stock_data(watchlist)
    return jsonify(data)

@app.route("/api/watchlist", methods=["POST"])
def add_watchlist():
    data = request.json
    ticker = data.get("ticker", "").strip().upper()
    name = data.get("name", "").strip()
    if ticker and name:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO watchlist VALUES (?, ?)', (ticker, name))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "잘못된 입력값입니다."}), 400

@app.route("/api/watchlist/<ticker>", methods=["DELETE"])
def remove_watchlist(ticker):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM watchlist WHERE ticker=?', (ticker,))
    if c.rowcount == 0:
        c.execute('DELETE FROM watchlist WHERE ticker=?', (ticker + '.KS',))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/search-stock", methods=["POST"])
def search_stock():
    data = request.json
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "error": "검색어를 입력해주세요."})
    
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "Gemini API Key가 설정되지 않아 검색 기능을 사용할 수 없습니다."})
        
    prompt = f"""
사용자가 입력한 주식 검색어: '{query}'
이 검색어에 해당하는 주식 시장의 Ticker 심볼(Yahoo Finance 기준)과 영문 공식 회사 이름을 찾아주세요.
관련된 종목이 있다면 가장 연관성이 높은 순서대로 1개에서 최대 3개까지 찾아주세요.
(한국 주식인 경우 KOSPI는 '.KS', 코스닥은 '.KQ'를 붙여주세요. 예: 005930.KS)
반드시 아래와 같은 JSON 배열 형식으로만 응답해야 합니다. 다른 텍스트는 절대로 포함하지 마세요:
[
  {{"ticker": "TSLA", "name": "Tesla, Inc."}}
]
"""
    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:-3]
        elif text.startswith('```'):
            text = text[3:-3]
            
        results = json.loads(text.strip())
        return jsonify({"success": True, "results": results})
    except Exception as e:
        print(f"Search API Error: {e}")
        return jsonify({"success": False, "error": "종목을 검색하는 데 실패했습니다. 다시 시도해주세요."})

@app.route("/api/portfolio-analysis", methods=["GET"])
def api_portfolio_analysis():
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "Gemini API Key가 설정되지 않았습니다."})
    
    watchlist = get_watchlist()
    if not watchlist:
        return jsonify({"success": True, "analysis": "관심 종목이 비어있습니다. 종목을 추가하시면 AI가 실시간으로 분석해 드립니다!"})
        
    data = fetch_stock_data(watchlist)
    
    # AI에게 보낼 종목 현황 텍스트 생성
    portfolio_text = "현재 관심 종목 (My Watchlist):\n"
    for item in data:
        sign = "+" if item['is_up'] else ""
        portfolio_text += f"- {item['name']} ({item['ticker']}): 현재가 {item['currency']}{item['price']}, 등락률 {sign}{item['change']}%\n"
        
    prompt = f"""
다음은 사용자의 현재 주식 관심 종목 리스트와 현재가, 등락률입니다.

{portfolio_text}

이 종목들을 포함한 관심 종목 포트폴리오의 **현재 상황 요약**과 **앞으로의 간략한 전망**을 작성해주세요. 
반드시 한국어로 자연스럽고 전문적으로 작성해주고, HTML 형태의 태그는 제외하고 평문으로 작성하세요. 너무 길지 않게 핵심만 2~3 문단(300자 내외)으로 요약해주세요.
또한 가장 주목할만한 종목 1개를 골라서 이유와 함께 짧게 추천해주세요.
"""

    try:
        response = gemini_client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
        )
        analysis_text = response.text
        return jsonify({"success": True, "analysis": analysis_text})
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({"success": False, "error": "AI 분석을 가져오는데 실패했습니다."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
