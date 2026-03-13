import yfinance as yf
try:
    print(yf.Ticker("465540.KS").info.get("shortName"))
except:
    pass
