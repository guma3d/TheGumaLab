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
import urllib.request
import xml.etree.ElementTree as ET

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
    try:
        c.execute('ALTER TABLE watchlist ADD COLUMN shares REAL DEFAULT 1')
    except sqlite3.OperationalError:
        pass  # Column already exists
    # 기본 종목 셋팅
    c.execute('SELECT count(*) FROM watchlist')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO watchlist (ticker, name, shares) VALUES (?, ?, ?)', [
            ('AAPL', 'Apple Inc.', 10),
            ('005930.KS', '삼성전자', 100),
            ('NVDA', 'NVIDIA', 5)
        ])
    conn.commit()
    conn.close()

init_db()

# 최신 분석 텍스트 저장용 (메모리)
latest_portfolio_analysis = "AI가 아직 관심 종목을 실시간 시장 현황을 바탕으로 분석하고 있습니다. 잠시만 기다려주세요..."

def get_watchlist():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT ticker, name, shares FROM watchlist')
    rows = c.fetchall()
    conn.close()
    return [{"ticker": r[0], "name": r[1], "shares": r[2]} for r in rows]

# 시장 지표 리스트
INDICES = [
    {"ticker": "^KS11", "name": "KOSPI"},
    {"ticker": "^KQ11", "name": "KOSDAQ"},
    {"ticker": "^IXIC", "name": "NASDAQ"},
    {"ticker": "^DJI", "name": "Dow Jones"},
    {"ticker": "^GSPC", "name": "S&P 500"}
]

def fetch_stock_data(tickers, force_refresh=False):
    """
    yfinance를 활용하여 현재가와 등락률을 반환합니다.
    """
    result = []
    for item in tickers:
        ticker = item["ticker"]
        name = item["name"]
        shares = item.get("shares", 0)

        
        # 캐시 확인 (만료 시간 설정 5분)
        cache_key = f"stock_data:{ticker}"
        if cache and not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                result.append(json.loads(cached_data))
                continue
                
        try:
            stock = yf.Ticker(ticker)
            current_price = None
            prev_close = None
            
            # 1. fast_info를 통해 장전/장후(프리마켓/애프터마켓) 실시간 가격 우선 추출
            try:
                current_price = getattr(stock.fast_info, 'lastPrice', stock.fast_info.get('lastPrice', None))
                prev_close = getattr(stock.fast_info, 'previousClose', stock.fast_info.get('previousClose', None))
            except Exception:
                pass
                
            # 2. fast_info 추출 실패 시 일반 history(prepost=True) 로 백업 데이터 호출
            if current_price is None or prev_close is None:
                hist = stock.history(period="5d", prepost=True)
                hist = hist.dropna(subset=['Close'])
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
            
            if current_price is not None and prev_close is not None:
                
                # 등락률 계산
                change_percent = ((current_price - prev_close) / prev_close) * 100
                
                data = {
                    "raw_ticker": ticker,
                    "ticker": ticker.replace(".KS", ""), # 한국 주식의 경우 UI 표시용으로 .KS 제거
                    "name": name,
                    "price": float(round(current_price, 2)),
                    "change": float(round(change_percent, 2)),
                    "is_up": bool(change_percent >= 0),
                    "currency": "₩" if any(x in ticker for x in [".KS", ".KQ", "^KS11", "^KQ11"]) else "$",
                    "shares": shares,
                    "total_value": round(current_price * shares, 2) if shares > 0 else 0.0
                }
            else:
                data = {
                    "raw_ticker": ticker,
                    "ticker": ticker.replace(".KS", ""),
                    "name": name,
                    "price": "N/A",
                    "change": 0.0,
                    "is_up": True,
                    "currency": "",
                    "shares": shares,
                    "total_value": 0.0
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
    shares = float(data.get("shares", 1))
    if ticker and name:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO watchlist (ticker, name, shares) VALUES (?, ?, ?)', (ticker, name, shares))
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
사용자가 입력한 주식 검색어 또는 주식 코드: '{query}'
이 검색어/코드에 해당하는 주식 시장의 Ticker 심볼(Yahoo Finance 기준)과 영문 공식 회사 이름을 찾아주세요. 

중요 지침:
1. 주식 코드(숫자 6자리)가 입력되면 반드시 해당 코드를 가진 종목을 최우선으로 찾아주세요.
2. 만약 '0118S0'와 같이 알파벳이 섞인 한국 ETF 증권사 단축 번호가 입력된 경우, 절대 비슷한 숫자의 일반 주식(예: STX)으로 혼동하지 마세요. 해당 번호가 지칭하는 정확한 ETF(예: SOL 미국넥스트테크TOP10액티브 등)를 파악하고, 그 ETF의 표준 6자리 거래 코드를 Yahoo Finance Ticker 형식으로 반환하세요.
3. 한국 주식인 경우 KOSPI는 '.KS', 코스닥은 '.KQ'를 Ticker에 붙여주세요. 숫자 코드가 중심이 된 경우 무조건 한국 주식입니다. 예: 005930 -> 005930.KS
4. 관련된 종목이 있다면 가장 연관성이 높은 순서대로 1개에서 최대 3개까지 찾아주세요.
5. 이 종목이 소속된 국가/시장을 'market' 필드에 '한국(KOR)' 또는 '미국(USA)' 등으로 명시해주세요.

반드시 아래와 같은 JSON 배열 형식으로만 응답해야 합니다. 다른 텍스트는 절대로 포함하지 마세요:
[
  {{"ticker": "TSLA", "name": "Tesla, Inc.", "market": "USA"}},
  {{"ticker": "446750.KS", "name": "SOL 미국넥스트테크TOP10액티브", "market": "KOR"}}
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

def fetch_latest_news_summary():
    urls = {
        "정치": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=ko&gl=KR&ceid=KR:ko",
        "경제": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
        "사회": "https://news.google.com/rss/headlines/section/topic/NATION?hl=ko&gl=KR&ceid=KR:ko",
        "주식": "https://news.google.com/rss/search?q=%EC%A3%BC%EC%8B%9D+when:24h&hl=ko&gl=KR&ceid=KR:ko",
        "IT": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko"
    }
    
    news_text = "최근 24시간 내 주요 뉴스 헤드라인 (각 분야별 5개, 총 25개):\n"
    for cat, url in urls.items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')[:5]
            news_text += f"\n[{cat}]\n"
            for item in items:
                title = item.find('title').text
                news_text += f"- {title}\n"
        except Exception as e:
            print(f"Error fetching news for {cat}: {e}")
            news_text += f"\n[{cat}] (뉴스 데이터를 불러올 수 없습니다)\n"
    return news_text

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
        portfolio_text = "현재 보유 포트폴리오 (My Portfolio):\n"
        for item in data:
            sign = "+" if item['is_up'] else ""
            portfolio_text += f"- {item['name']} ({item['ticker']}): {item['shares']}주 보유, 현재가 {item['currency']}{item['price']}, 등락률 {sign}{item['change']}%, 총 가치: {item['currency']}{item['total_value']}\n"
            
        news_summary = fetch_latest_news_summary()

        prompt = f"""
다음은 사용자의 현재 주식 관심 종목 리스트와 전체 포트폴리오 현황입니다.

{portfolio_text}

다음은 현재 24시간 내 발생한 공신력 있는 정치, 경제, 사회, 주식, IT 분야의 핵심 뉴스 헤드라인 25개입니다:
{news_summary}

이 종목들을 포함한 관심 종목 포트폴리오를 분석해주세요. 위 제공된 뉴스 데이터를 꼼꼼히 읽어보고 최신 정세와 뉴스를 분석 리포트에 반영해 주세요.
사용자가 한눈에 파악하기 쉽도록 **뛰어난 가독성**을 최우선으로 작성하는 것이 당신의 목표입니다.

**작성 지침 (필수):**
1. 빽빽한 줄글(문단)은 피하고, 핵심 내용 위주로 **불릿 포인트(-)** 형태를 적극 활용해 요약하세요.
2. 중요한 핵심 키워드, 기업명, 수익률, 추천 종목 등은 마크다운 굵게 표시(`**중요내용**`)를 사용하여 눈에 띄게 강조하세요.
3. 인상적인 인사이트나 최종 결론 등은 인용구(`> 문장`)를 섞어 가독성을 극대화하세요.
4. 반드시 다음 3가지 섹션으로 나누어 작성해야 하며, 각 섹션의 시작은 오직 대괄호를 사용한 지정된 영어 제목만 명시하세요 (`#` 등 기호 사용 불가):

[Current Portfolio Status]
현재 상황에 대한 핵심 요약 (불릿 포인트 적극 활용, 주요 수치 강조).

[Market News & Portfolio Direction]
제공된 뉴스를 바탕으로 한 현재 포트폴리오의 방향성 및 거시적/미시적 핵심 이슈 분석 (가독성 높은 형태로 정리).

[Recommended Modifications]
가장 주목할 만한 종목 1~2개를 골라 핵심 이유와 함께 추천하거나, 포트폴리오 개선 방향을 명확하게 제시 (리스트 형태 권장).

섹션 제목은 위에서 지정한 영어 텍스트 그대로 사용하시고, 다른 HTML 태그는 사용하지 마세요. 내용 본문은 한국어로 전문적으로 작성해 주세요.
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

# 백그라운드 스케줄러 등록 (5분 마다 최신 주가 동기화 및 AI 분석 처리 수행)
def background_sync_and_analyze():
    print("Background Sync & Analyze Started...")
    try:
        # 1. 최신 주가 정보 동기화 가동 (캐시 만료와 상관없이 즉시 갱신)
        fetch_stock_data(INDICES, force_refresh=True)
        watchlist = get_watchlist()
        if watchlist:
            fetch_stock_data(watchlist, force_refresh=True)
            
        # 2. 방금 갱신된 신선한 주가 데이터를 바탕으로 AI 분석 즉시 실시
        generate_portfolio_analysis()
    except Exception as e:
        print(f"Background Sync Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(background_sync_and_analyze, 'interval', minutes=5)
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
