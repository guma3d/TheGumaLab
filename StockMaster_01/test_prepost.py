import yfinance as yf

for ticker in ["AAPL", "^KS11", "005930.KS"]:
    stock = yf.Ticker(ticker)
    
    current_price = None
    prev_close = None
    
    try:
        # 1. fast_info 우선 확인 (장전/장후 시간외 거래 가격 포함)
        current_price = getattr(stock.fast_info, 'lastPrice', stock.fast_info.get('lastPrice', None))
        prev_close = getattr(stock.fast_info, 'previousClose', stock.fast_info.get('previousClose', None))
    except Exception:
        pass
        
    print(f"[{ticker}] current: {current_price}, prev: {prev_close}")
