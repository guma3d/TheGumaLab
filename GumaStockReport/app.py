# Auto-deploy test via GitHub Actions
from flask import Flask, render_template, jsonify, request, send_from_directory
import yfinance as yf
import redis
import json
import sqlite3
import os
from google import genai
from google.genai import types
from datetime import datetime
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import urllib.request
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 업로드 제한

# Redis 연결 (docker-compose의 서비스 이름 사용)
try:
    cache = redis.Redis(host='gumastockreport_redis', port=6379, db=0, decode_responses=True)
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

    # 포트폴리오 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS portfolios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT ''
    )''')

    # 기본 포트폴리오 4개 생성
    c.execute('SELECT count(*) FROM portfolios')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO portfolios (name, icon) VALUES (?, ?)', [
            ('나의 계좌', 'fa-user'),
            ('퇴직연금', 'fa-piggy-bank'),
            ('장준우', 'fa-child'),
            ('장지우', 'fa-child-reaching'),
        ])

    # watchlist 마이그레이션: portfolio_id 컬럼 없으면 테이블 재생성
    c.execute("PRAGMA table_info(watchlist)")
    columns = [col[1] for col in c.fetchall()]

    if not columns:
        # watchlist 테이블이 아예 없는 경우
        c.execute('''CREATE TABLE watchlist (
            portfolio_id INTEGER NOT NULL DEFAULT 1,
            ticker TEXT NOT NULL,
            name TEXT,
            shares REAL DEFAULT 1,
            PRIMARY KEY (portfolio_id, ticker),
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
        )''')
        c.executemany('INSERT INTO watchlist (portfolio_id, ticker, name, shares) VALUES (1, ?, ?, ?)', [
            ('AAPL', 'Apple Inc.', 10),
            ('005930.KS', '삼성전자', 100),
            ('NVDA', 'NVIDIA', 5)
        ])
    elif 'portfolio_id' not in columns:
        # 기존 테이블 → 마이그레이션
        c.execute('SELECT ticker, name, shares FROM watchlist')
        old_data = c.fetchall()
        c.execute('DROP TABLE watchlist')
        c.execute('''CREATE TABLE watchlist (
            portfolio_id INTEGER NOT NULL DEFAULT 1,
            ticker TEXT NOT NULL,
            name TEXT,
            shares REAL DEFAULT 1,
            PRIMARY KEY (portfolio_id, ticker),
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
        )''')
        for row in old_data:
            c.execute('INSERT INTO watchlist (portfolio_id, ticker, name, shares) VALUES (1, ?, ?, ?)', row)

    conn.commit()
    conn.close()

init_db()

# 최신 분석 텍스트 저장용 (메모리, 전체 종합)
latest_portfolio_analysis = ""
DEFAULT_ANALYSIS_MSG = "AI가 아직 관심 종목을 실시간 시장 현황을 바탕으로 분석하고 있습니다. 잠시만 기다려주세요..."

def get_all_portfolio_ids():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM portfolios')
    ids = [r[0] for r in c.fetchall()]
    conn.close()
    return ids

def get_watchlist(portfolio_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if portfolio_id:
        c.execute('SELECT ticker, name, shares FROM watchlist WHERE portfolio_id=?', (portfolio_id,))
    else:
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

        # 현금성 자산 처리 (예수금, 외화예수금)
        if ticker.startswith('CASH_'):
            currency_code = ticker[5:]
            currency_map = {'KRW': '₩', 'USD': '$', 'EUR': '€', 'JPY': '¥', 'GBP': '£', 'CNY': '¥'}
            currency_symbol = currency_map.get(currency_code, currency_code + ' ')
            data = {
                "raw_ticker": ticker,
                "ticker": ticker,
                "name": name,
                "price": None,
                "change": 0.0,
                "is_up": True,
                "currency": currency_symbol,
                "shares": shares,
                "total_value": round(float(shares), 2),
                "is_cash": True
            }
            if cache:
                cache.setex(cache_key, 300, json.dumps(data))
            result.append(data)
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

@app.route("/sw.js")
def serve_sw():
    # Serve Service Worker from the frontend root with proper MIME type
    response = send_from_directory("frontend", "sw.js")
    response.headers['Content-Type'] = 'application/javascript'
    # Ensure Service-Worker-Allowed header is set
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route("/frontend/<path:filename>")
def serve_frontend(filename):
    return send_from_directory("frontend", filename)

@app.route("/api/portfolios", methods=["GET"])
def api_portfolios():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, icon FROM portfolios ORDER BY id')
    rows = c.fetchall()
    conn.close()
    return jsonify([{"id": r[0], "name": r[1], "icon": r[2]} for r in rows])

@app.route("/api/market-indices")
def api_market_indices():
    data = fetch_stock_data(INDICES)
    return jsonify(data)

@app.route("/api/watchlist", methods=["GET"])
def api_watchlist():
    portfolio_id = request.args.get("portfolio_id", 1, type=int)
    watchlist = get_watchlist(portfolio_id)
    data = fetch_stock_data(watchlist)
    return jsonify(data)

@app.route("/api/watchlist", methods=["POST"])
def add_watchlist():
    data = request.json
    ticker = data.get("ticker", "").strip().upper()
    name = data.get("name", "").strip()
    shares = float(data.get("shares", 1))
    portfolio_id = int(data.get("portfolio_id", 1))
    if ticker and name:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO watchlist (portfolio_id, ticker, name, shares) VALUES (?, ?, ?, ?)',
                  (portfolio_id, ticker, name, shares))
        conn.commit()
        conn.close()
        trigger_analysis_bg()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "잘못된 입력값입니다."}), 400

@app.route("/api/watchlist/<ticker>", methods=["DELETE"])
def remove_watchlist(ticker):
    portfolio_id = request.args.get("portfolio_id", 1, type=int)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM watchlist WHERE portfolio_id=? AND ticker=?', (portfolio_id, ticker))
    if c.rowcount == 0:
        c.execute('DELETE FROM watchlist WHERE portfolio_id=? AND ticker=?', (portfolio_id, ticker + '.KS'))
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

@app.route("/api/parse-screenshot", methods=["POST"])
def parse_screenshot():
    """삼성증권 스크린샷에서 보유 종목 정보를 Gemini Vision으로 추출"""
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "이미지를 업로드해주세요."}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "파일이 선택되지 않았습니다."}), 400

    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "Gemini API Key가 설정되지 않아 이미지 분석을 사용할 수 없습니다."}), 500

    image_bytes = file.read()
    mime_type = file.content_type or 'image/jpeg'

    prompt = """이 이미지는 삼성증권 모바일 앱의 보유종목 화면 캡처입니다.
이미지에서 다음 두 가지를 모두 추출해주세요.

[1] 보유 종목 (stocks):
- name: 종목명 (이미지에 표시된 그대로)
- code: 종목코드 (6자리 숫자). 이미지에 있으면 그대로, 없으면 종목명으로 유추. 미국 주식은 ticker 심볼(AAPL 등)
- shares: 보유수량 (정수). 쉼표 제거
- market: 'KOSPI' / 'KOSDAQ' / 'US'
- ETF, 펀드 포함. 현금성 항목(예수금, 외화예수금, RP 등)은 제외

[2] 현금성 자산 (cash):
- 예수금 / 원화예수금 / 현금잔고 → currency: "KRW"
- 달러예수금 / USD 외화예수금 → currency: "USD"
- 기타 외화예수금 → currency에 통화코드 (EUR, JPY, GBP 등)
- name: 이미지에 표시된 항목명 그대로
- amount: 금액 (소수점 허용, 쉼표 제거)
- 현금성 자산이 없으면 cash는 빈 배열 []

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요:
{
  "stocks": [
    {"name": "삼성전자", "code": "005930", "shares": 100, "market": "KOSPI"}
  ],
  "cash": [
    {"name": "예수금", "currency": "KRW", "amount": 1500000},
    {"name": "외화예수금", "currency": "USD", "amount": 1000.5}
  ]
}

이미지에서 종목·현금 정보를 전혀 찾을 수 없다면:
{"error": "이미지에서 정보를 찾을 수 없습니다. 삼성증권 보유종목 화면을 캡처해주세요."}
"""

    try:
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt],
        )

        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]

        result = json.loads(text.strip())

        if isinstance(result, dict) and 'error' in result:
            return jsonify({"success": False, "error": result['error']})

        # 구 포맷(list) / 신 포맷(object) 모두 지원
        stock_list = result if isinstance(result, list) else result.get('stocks', [])
        cash_list = [] if isinstance(result, list) else result.get('cash', [])

        # 종목코드 → Yahoo Finance ticker 변환
        stocks = []
        for stock in stock_list:
            code = str(stock.get('code', '')).strip()
            name = stock.get('name', '').strip()
            shares = int(float(stock.get('shares', 0)))
            market = stock.get('market', 'KOSPI').upper()

            if market == 'US':
                ticker = code
            elif market == 'KOSDAQ':
                ticker = f"{code.zfill(6)}.KQ"
            else:
                ticker = f"{code.zfill(6)}.KS"

            stocks.append({"name": name, "code": code, "ticker": ticker, "shares": shares, "market": market})

        # 현금성 자산 변환
        cash = []
        for item in cash_list:
            currency = item.get('currency', 'KRW').upper()
            name = item.get('name', '예수금').strip()
            amount = float(item.get('amount', 0))
            cash.append({
                "name": name,
                "currency": currency,
                "ticker": f"CASH_{currency}",
                "amount": amount
            })

        if not stocks and not cash:
            return jsonify({"success": False, "error": "종목 및 현금 정보를 찾을 수 없습니다."})

        return jsonify({"success": True, "stocks": stocks, "cash": cash})
    except json.JSONDecodeError:
        print(f"Screenshot parse JSON error. Raw text: {text}")
        return jsonify({"success": False, "error": "이미지 분석 결과를 파싱할 수 없습니다. 다시 시도해주세요."})
    except Exception as e:
        print(f"Screenshot parse error: {e}")
        return jsonify({"success": False, "error": "스크린샷 분석에 실패했습니다. 다시 시도해주세요."})


@app.route("/api/import-portfolio", methods=["POST"])
def import_portfolio():
    """파싱된 종목 데이터를 포트폴리오에 일괄 반영"""
    data = request.json
    stocks = data.get("stocks", [])
    mode = data.get("mode", "merge")  # "replace": 기존 전체 교체, "merge": 기존에 합치기
    portfolio_id = int(data.get("portfolio_id", 1))

    if not stocks:
        return jsonify({"success": False, "error": "가져올 종목 데이터가 없습니다."}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if mode == "replace":
        c.execute('DELETE FROM watchlist WHERE portfolio_id=?', (portfolio_id,))

    imported = 0
    for stock in stocks:
        ticker = stock.get('ticker', '').strip()
        name = stock.get('name', '').strip()
        shares = float(stock.get('shares', 1))
        if ticker and name:
            c.execute('INSERT OR REPLACE INTO watchlist (portfolio_id, ticker, name, shares) VALUES (?, ?, ?, ?)',
                      (portfolio_id, ticker, name, shares))
            imported += 1

    conn.commit()
    conn.close()
    trigger_analysis_bg()

    return jsonify({"success": True, "imported": imported})


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

def get_all_portfolios_with_stocks():
    """전체 포트폴리오와 종목을 계좌별로 그룹핑해서 반환"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT p.name, w.ticker, w.name, w.shares
                 FROM portfolios p
                 LEFT JOIN watchlist w ON p.id = w.portfolio_id
                 ORDER BY p.id, w.name''')
    rows = c.fetchall()
    conn.close()

    portfolios = {}
    for pname, ticker, sname, shares in rows:
        if pname not in portfolios:
            portfolios[pname] = []
        if ticker:
            portfolios[pname].append({"ticker": ticker, "name": sname, "shares": shares})
    return portfolios

def generate_portfolio_analysis():
    global latest_portfolio_analysis
    cache_key = "portfolio_analysis"

    if not GEMINI_API_KEY:
        msg = "Gemini API Key가 설정되지 않았습니다."
        latest_portfolio_analysis = msg
        if cache:
            cache.set(cache_key, msg)
        return

    all_portfolios = get_all_portfolios_with_stocks()
    all_stocks = []
    for stocks in all_portfolios.values():
        all_stocks.extend(stocks)

    if not all_stocks:
        msg = "관심 종목이 비어있습니다. 종목을 추가하시면 AI가 5분 단위로 시장을 분석해 드립니다!"
        latest_portfolio_analysis = msg
        if cache:
            cache.set(cache_key, msg)
        return

    try:
        data = fetch_stock_data(all_stocks)
        # ticker → 실시간 가격 매핑
        price_map = {item['raw_ticker']: item for item in data}

        portfolio_text = ""
        for pname, stocks in all_portfolios.items():
            if not stocks:
                continue
            portfolio_text += f"\n[{pname}]\n"
            for s in stocks:
                info = price_map.get(s['ticker'], {})
                if info.get('is_cash'):
                    portfolio_text += f"- {s['name']}: 잔고 {info.get('currency','')}{info.get('total_value', s['shares'])}\n"
                else:
                    sign = "+" if info.get('is_up', True) else ""
                    portfolio_text += f"- {s['name']} ({info.get('ticker', s['ticker'])}): {s['shares']}주 보유, 현재가 {info.get('currency','')}{info.get('price','N/A')}, 등락률 {sign}{info.get('change',0)}%, 총 가치: {info.get('currency','')}{info.get('total_value',0)}\n"

        news_summary = fetch_latest_news_summary()

        prompt = f"""
다음은 사용자가 관리하는 전체 주식 포트폴리오 현황입니다. 여러 계좌로 나뉘어 있지만 하나의 종합 포트폴리오로 분석해주세요.

{portfolio_text}

다음은 현재 24시간 내 발생한 공신력 있는 정치, 경제, 사회, 주식, IT 분야의 핵심 뉴스 헤드라인 25개입니다:
{news_summary}

위 모든 계좌의 종목을 통합하여 하나의 종합 포트폴리오로 분석해주세요. 위 제공된 뉴스 데이터를 꼼꼼히 읽어보고 최신 정세와 뉴스를 분석 리포트에 반영해 주세요.
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
            cache.set(cache_key, response.text, ex=600)  # 10분 TTL
        print("Background AI Portfolio Analysis Updated (combined).")
    except Exception as e:
        print(f"Background AI Error: {e}")

# 백그라운드 스케줄러 등록 (5분 마다 최신 주가 동기화 및 AI 분석 처리 수행)
def background_sync_and_analyze():
    print("Background Sync & Analyze Started...")
    try:
        # 1. 최신 주가 정보 동기화 가동 (캐시 만료와 상관없이 즉시 갱신)
        fetch_stock_data(INDICES, force_refresh=True)
        all_watchlist = get_watchlist()  # 전체 종목 갱신
        if all_watchlist:
            fetch_stock_data(all_watchlist, force_refresh=True)

        # 2. 전체 포트폴리오 종합 AI 분석
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
    cache_key = "portfolio_analysis"

    analysis_text = None
    if cache:
        cached = cache.get(cache_key)
        if cached:
            analysis_text = cached

    if not analysis_text:
        analysis_text = latest_portfolio_analysis if isinstance(latest_portfolio_analysis, str) else DEFAULT_ANALYSIS_MSG

    return jsonify({"success": True, "analysis": analysis_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
