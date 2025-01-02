import yfinance as yf
from blessed import Terminal
import time
import numpy as np

# Constants
UPDATE_INTERVAL = 5  # seconds
DEFAULT_STOCKS = ["^DJI", "^GSPC", "^IXIC", "^N225","000001.SS" ,"BTC-USD"]  # Dow, S&P 500, Nasdaq, Nikkei, Shanghai Composite, Bitcoin

def fetch_stock_data(tickers):
    """Fetch stock data for the given tickers."""
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d", interval="5m")
            price = stock.info.get("regularMarketPrice") or stock.info.get("previousClose")
            if hist.empty:
                data[ticker] = {
                    "price": price,
                    "chart": []
                }
            else:
                chart = hist["Close"].tolist()
                data[ticker] = {
                    "price": price,
                    "chart": chart[-25:]  # Last 25 data points
                }
        except Exception as e:
            data[ticker] = {
                "price": "N/A",
                "chart": []
            }
    return data

def render_chart(prices, width, height=5):
    """Render a traditional stock line chart."""
    if not prices:
        return [" " * width for _ in range(height)]

    min_price = min(prices)
    max_price = max(prices)
    scale = (max_price - min_price) if max_price != min_price else 1
    scaled_prices = [int((p - min_price) / scale * (height - 1)) for p in prices]

    # Initialize a blank grid
    chart = [[" " for _ in range(width)] for _ in range(height)]

    # Plot the points and connect them
    for i in range(len(scaled_prices) - 1):
        y1 = height - 1 - scaled_prices[i]  # Invert y-axis for terminal rendering
        y2 = height - 1 - scaled_prices[i + 1]
        x1 = min(int(i * (width / (len(scaled_prices) - 1))), width - 1)
        x2 = min(int((i + 1) * (width / (len(scaled_prices) - 1))), width - 1)

        # Draw the line
        if x1 == x2:  # Vertical line
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= y < height:
                    chart[y][x1] = "|"
        else:  # Diagonal or horizontal line
            slope = (y2 - y1) / (x2 - x1)
            for x in range(x1, x2 + 1):
                if 0 <= x < width:
                    y = round(y1 + slope * (x - x1))
                    if 0 <= y < height:
                        chart[y][x] = "*"

    # Convert rows to strings
    return ["".join(row) for row in chart]

def render_grid(term, data):
    """Render the grid of stocks."""
    rows, cols = term.height - 2, term.width
    grid_width = max(cols // 2, 20)  # Each square takes half the screen width or 20 chars
    grid_height = max(rows // len(data), 8)  # Each square takes equal height or 8 lines

    output = []
    for i, (ticker, info) in enumerate(data.items()):
        x = (i % 2) * grid_width  # Two columns
        y = (i // 2) * grid_height

        price = info["price"]
        chart = render_chart(info["chart"], grid_width - 2, grid_height - 3)

        color = term.green if isinstance(price, (int, float)) and price >= 0 else term.red
        price_text = color(f"Price: {price}") if price != "N/A" else term.yellow("Price: N/A")

        output.append(term.move_xy(x, y) + term.bold(f"{ticker}"))
        output.append(term.move_xy(x, y + 1) + price_text)
        for j, line in enumerate(chart):
            output.append(term.move_xy(x, y + 2 + j) + term.cyan(line))

    return "\n".join(output)

def main():
    term = Terminal()
    stocks = DEFAULT_STOCKS

    with term.fullscreen(), term.hidden_cursor():
        while True:
            try:
                data = fetch_stock_data(stocks)
                with term.location(0, 0):
                    print(term.clear() + render_grid(term, data))
                time.sleep(UPDATE_INTERVAL)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()
