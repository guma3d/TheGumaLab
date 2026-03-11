import yfinance as yf
try:
    stock = yf.Ticker("^KS11")
    hist = stock.history(period="5d")
    hist = hist.dropna(subset=['Close'])
    print(len(hist))
    current_price = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2]
    change_percent = ((current_price - prev_close) / prev_close) * 100
    print("current: ", current_price, "change:", change_percent)
except Exception as e:
    import traceback
    traceback.print_exc()
