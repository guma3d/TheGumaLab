from flask import Flask, render_template, jsonify
import yfinance as yf
import redis
import json
import sqlite3
import os
from google import genai
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import threading
from apscheduler.schedulers.background import BackgroundScheduler

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

# 최신 분석 텍스트 저장용 (메모리)
latest_portfolio_analysis = "AI가 아직 관심 종목을 실시간 시장 현황을 바탕으로 분석하고 있습니다. 잠시만 기다려주세요..."

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
        trigger_analysis_bg()
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
    trigger_analysis_bg()
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

def generate_portfolio_analysis():
    global latest_portfolio_analysis
    if not GEMINI_API_KEY:
        latest_portfolio_analysis = "Gemini API Key가 설정되지 않았습니다."
        if cache:
            cache.set("portfolio_analysis", latest_portfolio_analysis)
        return

    watchlist = get_watchlist()
    if not watchlist:
        latest_portfolio_analysis = "관심 종목이 비어있습니다. 종목을 추가하시면 AI가 5분 단위로 시장을 분석해 드립니다!"
        if cache:
            cache.set("portfolio_analysis", latest_portfolio_analysis)
        return
        
    try:
        data = fetch_stock_data(watchlist)
        portfolio_text = "현재 관심 종목 (My Watchlist):\n"
        for item in data:
            sign = "+" if item['is_up'] else ""
            portfolio_text += f"- {item['name']} ({item['ticker']}): 현재가 {item['currency']}{item['price']}, 등락률 {sign}{item['change']}%\n"
            
        prompt = f"""
다음은 사용자의 현재 주식 관심 종목 리스트와 현재가, 등락률입니다.

{portfolio_text}

이 종목들을 포함한 관심 종목 포트폴리오를 분석해주세요.
반드시 다음 두 가지 섹션으로 나누어 작성해주시고, 각 섹션의 시작은 대괄호를 사용한 지정된 제목으로 명시해주세요:

[Current Portfolio Status]
현재 상황에 대한 핵심 요약 2~3 문단(300자 내외).

[Recommended Modifications]
가장 주목할 만한 종목 1개를 골라서 이유와 함께 추천하거나, 포트폴리오의 개선 방향을 짧게 제시.

단, 앞으로의 일반적인 전망(Outlook)에 대한 내용은 제외해주세요.
HTML 태그 없이 평문으로 한국어로 전문적으로 작성하되, 섹션 제목만 위에서 지정한 영어 텍스트 그대로 사용하세요.
"""
        response = gemini_client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=prompt,
        )
        
        latest_portfolio_analysis = response.text
        if cache:
            cache.set("portfolio_analysis", latest_portfolio_analysis, ex=600)  # 10분 TTL
        print("Background AI Portfolio Analysis Updated.")
    except Exception as e:
        print(f"Background AI Error: {e}")

# 백그라운드 스케줄러 등록 (5분 마다 AI 분석 실행)
scheduler = BackgroundScheduler()
scheduler.add_job(generate_portfolio_analysis, 'interval', minutes=5)
scheduler.start()

def trigger_analysis_bg():
    # 사용자가 종목을 추가/삭제할 때만 별도 스레드로 AI 분석 즉시 업데이트
    thread = threading.Thread(target=generate_portfolio_analysis)
    thread.start()

# 최초 1회 분석 돌려놓기
trigger_analysis_bg()

@app.route("/api/portfolio-analysis", methods=["GET"])
def api_portfolio_analysis():
    analysis_text = None
    if cache:
        cached = cache.get("portfolio_analysis")
        if cached:
            analysis_text = cached
            
    if not analysis_text:
        analysis_text = latest_portfolio_analysis
        
    return jsonify({"success": True, "analysis": analysis_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
