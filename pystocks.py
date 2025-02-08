from bs4 import BeautifulSoup
import requests
import yfinance
from blessed import Terminal
import time

# Default stocks
DEFAULT_STOCKS = {
    "SPY": "S&P 500",
    "QQQ": "NASDAQ",
    "^N225": "Nikkei 225",
    "BTC-USD": "Bitcoin",
    "GLD": "Gold",
    "USO": "Oil"
}


def get_quotes(tickers):
        # Fetch and store stock quotes scraped from yahoo finance
    stock_prices = {}
    for ticker in tickers:
        url = (f"https://finance.yahoo.com/quote/{ticker}/")
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tag = soup.find('span', class_='base yf-ipw1h0')
            if tag:
                stock_prices[ticker] = float(tag.decode_contents().replace(',', ''))
            else:
                stock_prices[ticker] = "N/A"
        else:
            stock_prices[ticker] = "N/A"
    return stock_prices


def get_history(ticker): # gathers historical stock prices
    stock = yfinance.Ticker(ticker)
    history = stock.history(period="1d", interval="15m")["Close"]
    return history.tolist()


def render_chart(prices, width, height=5): # draws chart for stock history #claudeai helped with this function
    """Render a traditional stock line chart."""
    if not prices:
        return [" " * width for _ in range(height)]

    min_price = min(prices)
    max_price = max(prices)
    scale = (max_price - min_price) if max_price != min_price else 1
    scaled_prices = [int((p - min_price) / scale * (height - 1)) for p in prices]

    chart = [[" " for _ in range(width)] for _ in range(height)]

    for i in range(len(scaled_prices) - 1):
        y1 = height - 1 - scaled_prices[i]
        y2 = height - 1 - scaled_prices[i + 1]
        x1 = min(int(i * (width / (len(scaled_prices) - 1))), width - 1)
        x2 = min(int((i + 1) * (width / (len(scaled_prices) - 1))), width - 1)

        if x1 == x2:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= y < height:
                    chart[y][x1] = "|"
        else:
            slope = (y2 - y1) / (x2 - x1)
            for x in range(x1, x2 + 1):
                if 0 <= x < width:
                    y = round(y1 + slope * (x - x1))
                    if 0 <= y < height:
                        chart[y][x] = "*"

    return ["".join(row) for row in chart]


def render_grid(term, data, stocks, status_message=""):
    """Render the grid of stocks."""
    # Reserve space for status area at bottom (commands, status message, timestamp)
    bottom_margin = 4
    top_margin = 1  # Add margin at top

    # Calculate available space for grid
    rows = term.height - bottom_margin - top_margin
    cols = term.width

    grid_width = max(cols // 2, 30)
    grid_height = max(rows // ((len(data) + 1) // 2), 8)

    output = []

    # Start drawing from top margin
    for i, (ticker, info) in enumerate(data.items()):
        x = (i % 2) * grid_width
        y = (i // 2) * grid_height + top_margin  # Add top margin to y position

        price = info["price"]
        chart = render_chart(info["chart"], grid_width - 2, grid_height - 3)

        display_name = f"{stocks.get(ticker, ticker)} ({ticker})"

        color = term.green if isinstance(price, (int, float)) and price >= 0 else term.red
        price_text = color(f"Price: {price}") if price != "N/A" else term.yellow("Price: N/A")

        output.append(term.move_xy(x, y) + term.bold(display_name))
        output.append(term.move_xy(x, y + 1) + price_text)
        for j, line in enumerate(chart):
            output.append(term.move_xy(x, y + 2 + j) + term.cyan(line))

    # Add bottom status area
    bottom_y = term.height - bottom_margin
    commands = term.move_xy(0, bottom_y) + \
        term.white("Commands: (a)dd stock, (r)emove stock, (u)pdate, (q)uit")
    status = term.move_xy(0, bottom_y + 1) + term.yellow(status_message)
    timestamp = term.move_xy(0, bottom_y + 2) + \
        term.white(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    output.extend([commands, status, timestamp])
    return "\n".join(output)


def main(): # Main function
    term = Terminal()
    stocks = dict(DEFAULT_STOCKS)  # Make a copy of the initial indices
    data = {}

    print("Starting market index viewer...")

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while True:
            # Update the display
            prices = get_quotes(list(stocks.keys()))
            for ticker in stocks.keys():
                try:
                    history = get_history(ticker)
                    data[ticker] = {
                        "price": prices[ticker],
                        "chart": history
                    }
                except Exception as e:
                    data[ticker] = {
                        "price": "N/A",
                        "chart": []
                    }

            # Show the current state
            print(term.clear + render_grid(term, data, stocks))

            # Get user command
            key = term.inkey()

            if key.lower() == 'q':
                break
            elif key.lower() == 'a':
                # Add a stock
                print(term.move_xy(0, term.height - 1) + term.clear_eol +
                      "Enter ticker symbol: ", end='', flush=True)
                ticker = input().strip().upper()
                if ticker:
                    stocks[ticker] = ticker  # Use ticker as name if not an index
                    status_message = f"Added {ticker}"
                else:
                    status_message = "No ticker entered"
            elif key.lower() == 'r':
                # Remove a stock
                print(term.move_xy(0, term.height - 1) + term.clear_eol +
                      "Enter ticker to remove: ", end='', flush=True)
                ticker = input().strip().upper()
                if ticker in stocks:
                    del stocks[ticker]
                    data.pop(ticker, None)
                    status_message = f"Removed {ticker}"
                else:
                    status_message = f"Ticker {ticker} not found"
            elif key.lower() == 'u':
                status_message = "Updating..."
            else:
                status_message = "Press a key to update or use commands: (a)dd, (r)emove, (u)pdate, (q)uit"


if __name__ == "__main__":
    main()
