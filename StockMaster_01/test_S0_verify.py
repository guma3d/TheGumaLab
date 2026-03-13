import yfinance as yf
try:
    print(yf.Ticker("446750.KS").history(period="1d"))
except Exception as e:
    print(e)
