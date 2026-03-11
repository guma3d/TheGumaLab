import yfinance as yf
print("KOSPI:")
try:
    print(yf.Ticker("^KS11").history(period="5d"))
except Exception as e:
    print("Error KS11:", e)

print("\nKOSDAQ:")
try:
    print(yf.Ticker("^KQ11").history(period="5d"))
except Exception as e:
    print("Error KQ11:", e)
