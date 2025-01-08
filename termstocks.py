import yfinance as yf
from blessed import Terminal
import time
import numpy as np
import math

# Constants
UPDATE_INTERVAL = 10  # seconds
DEFAULT_STOCKS = ["^DJI", "SPY", "^QQQ", "^N225", "000001.SS", "BTC-USD"]  # Dow, S&P 500, Nasdaq, Nikkei, Shanghai Composite, Bitcoin
COMMAND_AREA_HEIGHT = 2  # Height reserved for commands and input

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

def render_chart(prices, width, height=6):
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

def calculate_grid_layout(term, num_stocks):
    """Calculate the optimal grid layout based on terminal size and number of stocks."""
    available_height = term.height - COMMAND_AREA_HEIGHT
    available_width = term.width

    # Determine number of columns (max 2)
    num_columns = min(2, num_stocks)
    if num_columns == 0:
        num_columns = 1

    # Calculate number of rows needed
    num_rows = math.ceil(num_stocks / num_columns)

    # Calculate individual cell dimensions
    cell_width = available_width // num_columns
    cell_height = available_height // num_rows if num_rows > 0 else available_height

    return {
        'num_columns': num_columns,
        'num_rows': num_rows,
        'cell_width': cell_width,
        'cell_height': cell_height
    }

def render_grid(term, data):
    """Render the grid of stocks."""
    if not data:
        return ""

    layout = calculate_grid_layout(term, len(data))
    output = []

    # Calculate chart height (leaving room for ticker and price)
    chart_height = layout['cell_height'] - 3  # 2 lines for ticker/price, 1 line padding

    for i, (ticker, info) in enumerate(data.items()):
        # Calculate position
        col = i % layout['num_columns']
        row = i // layout['num_columns']
        
        x = col * layout['cell_width']
        y = row * layout['cell_height']

        price = info["price"]
        chart = render_chart(info["chart"], layout['cell_width'] - 2, chart_height)

        color = term.green if isinstance(price, (int, float)) and price >= 0 else term.lightcoral
        price_text = color(f"Price: {price}") if price != "N/A" else term.yellow("Price: N/A")

        # Add padding to prevent text overlap
        ticker_display = f"{ticker:<{layout['cell_width']}}"
        price_display = f"{price_text:<{layout['cell_width']}}"

        output.append(term.move_xy(x, y) + term.bold(ticker_display))
        output.append(term.move_xy(x, y + 1) + price_display)
        
        for j, line in enumerate(chart):
            padded_line = f"{line:<{layout['cell_width']}}"
            output.append(term.move_xy(x, y + 2 + j) + term.lightseagreen(padded_line))

    # Add command help at the bottom
    help_text = "Commands: (a)dd ticker, (r)emove ticker, (q)uit"
    output.append(term.move_xy(0, term.height - COMMAND_AREA_HEIGHT) + term.black_on_white(help_text))
    # Add a clear line below the help text for input area
    # output.append(term.move_xy(0, term.height - 1) + term.clear_eol)

    return "\n".join(output)

def add_ticker(term, stocks):
    """Prompt user to add a new ticker."""
    with term.location(0, term.height - 1):
        print(term.clear_eol + "Enter ticker symbol to add: ", end="", flush=True)
        ticker = input().strip().upper()
        if ticker and ticker not in stocks:
            try:
                # Verify ticker exists by attempting to fetch data
                stock = yf.Ticker(ticker)
                stock.info
                stocks.append(ticker)
                print(term.clear_eol + f"Added {ticker}")
            except Exception as e:
                print(term.clear_eol + f"Error: Could not find ticker {ticker}")
        time.sleep(1)

def remove_ticker(term, stocks):
    """Prompt user to remove a ticker."""
    with term.location(0, term.height - 1):
        print(term.clear_eol + "Enter ticker symbol to remove: ", end="", flush=True)
        ticker = input().strip().upper()
        if ticker in stocks:
            stocks.remove(ticker)
            print(term.clear_eol + f"Removed {ticker}")
        else:
            print(term.clear_eol + f"Ticker {ticker} not found")
        time.sleep(1)

def main():
    term = Terminal()
    stocks = DEFAULT_STOCKS.copy()

    with term.fullscreen(), term.cbreak():
        while True:
            try:
                # Check for keyboard input
                if term.inkey(timeout=0):
                    key = term.inkey()
                    if key.lower() == 'q':
                        break
                    elif key.lower() == 'a':
                        add_ticker(term, stocks)
                    elif key.lower() == 'r':
                        remove_ticker(term, stocks)

                # Update display
                data = fetch_stock_data(stocks)
                with term.location(0, 0):
                    print(term.clear() + render_grid(term, data))
                time.sleep(UPDATE_INTERVAL)
            except KeyboardInterrupt:
                break

if __name__ == "__main__":
    main()

