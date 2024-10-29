Write a linkedin post for the following python tool. 
import yfinance as yf
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich import box
import time
import requests
import pandas as pd
from io import StringIO
import shutil

# Function to get S&P 500 tickers
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    tables = pd.read_html(StringIO(response.text))
    sp500_table = tables[0]
    tickers = sp500_table['Symbol'].tolist()
    return tickers

# Function to get stock data
def get_stock_data(tickers):
    stock_data = []
    for ticker in tickers:
        stock_info = yf.Ticker(ticker).info
        data = yf.Ticker(ticker).history(period="1d")
        # Get the opening and current/last closing prices
        # Check if data is not empty
        if data.empty:
            print(f"No data available for {ticker}")
            continue

        opening_price = data['Open'].iloc[0]
        current_price = data['Close'].iloc[-1]
        stock_data.append({
            "ticker" : ticker,
            "name": stock_info.get("shortName", ticker),
            "price": current_price,
            "change": ((current_price - opening_price) / opening_price) * 100,
            "volume": stock_info.get("regularMarketVolume", 0),
            "market_cap": stock_info.get("marketCap", 0)
        })
    return stock_data

# Function to select 25 top gainers + 25 biggest loser + 15 largest market cap + 20 highest volume
# Keep these stock tickers in a separate list and refresh information of this list at each auto refresh
# to populate tables
def get_filtered_stock_tickers(stock_data):
    stock_over_ten = [stock for stock in stock_data if stock["price"] > 10]
    gainer_list = sorted(stock_over_ten, key=lambda x: x["change"], reverse=True)[:25]
    loser_list = sorted(stock_over_ten, key=lambda x: x["change"])[:25]
    volume_list = sorted(stock_data, key=lambda x: x["volume"], reverse=True)[:20]
    market_cap_list = sorted(stock_data, key=lambda x: x["market_cap"], reverse=True)[:15]
    filtered_stock_tickers = []
    filtered_stock_tickers.extend([x["ticker"] for x in gainer_list])
    filtered_stock_tickers.extend([x["ticker"] for x in loser_list])
    filtered_stock_tickers.extend([x["ticker"] for x in volume_list])
    filtered_stock_tickers.extend([x["ticker"] for x in market_cap_list])
    return filtered_stock_tickers


# Function to create tables
def create_tables(stock_data):
    # Get terminal size
    size = shutil.get_terminal_size()
    # Width (columns) and height (rows)
    width = size.columns
    height = size.lines
    #print(f"Width: {width}, Height: {height}")

    # Filter stocks with price greater than 10 USD for gainers and losers
    filtered_data = [stock for stock in stock_data if stock["price"] > 10]

    # Sort data for each table
    gainers = sorted(filtered_data, key=lambda x: x["change"], reverse=True)[:10]
    losers = sorted(filtered_data, key=lambda x: x["change"])[:10]
    volume = sorted(stock_data, key=lambda x: x["volume"], reverse=True)[:10]
    market_cap = sorted(stock_data, key=lambda x: x["market_cap"], reverse=True)[:10]

    # Create tables
    # 2 tables side by side. Width of name, price and change would be 50%,25% and 25% respectively
    gainers_table_width = (width - 10) // 2;
    gainers_table = Table(title="Top 10 Gainers", box=box.SQUARE)
    gainers_table.add_column("Stock Name", style="cyan", width=gainers_table_width//2)
    gainers_table.add_column("Current Price", style="green", width=gainers_table_width//4)
    gainers_table.add_column("Change %", style="red", width=gainers_table_width//4)

    for gainer in gainers:
        gainers_table.add_row(gainer["name"], f"{gainer['price']:.4f}$", f"{gainer['change']:.2f}%")

    # 2 tables side by side. Width of name, price and change would be 50%,25% and 25% respectively
    losers_table_width = (width - 10) // 2;
    losers_table = Table(title="Top 10 Losers", box=box.SQUARE)
    losers_table.add_column("Stock Name", style="cyan", width=losers_table_width//2)
    losers_table.add_column("Current Price", style="red", width=losers_table_width//4)
    losers_table.add_column("Change %", style="blue", width=losers_table_width//4)

    for loser in losers:
        losers_table.add_row(loser["name"], f"{loser['price']:.4f}$", f"{loser['change']:.2f}%")

    # 2 tables side by side. Width of name, price and change would be 50%,25% and 25% respectively
    volume_table_width = (width -10)//2
    volume_table = Table(title="Top 10 by Volume", box=box.SQUARE)
    volume_table.add_column("Stock Name", style="cyan", width=volume_table_width*3//5)
    volume_table.add_column("Volume", style="yellow", width=volume_table_width*2//5)

    for vol in volume:
        volume_table.add_row(vol["name"], str(vol["volume"]))

    # 2 tables side by side. Width of name, price and change would be 50%,25% and 25% respectively
    market_cap_table_width = (width -10)//2
    market_cap_table = Table(title="Top 10 by Market Cap", box=box.SQUARE)
    market_cap_table.add_column("Stock Name", style="cyan", width=market_cap_table_width//2)
    market_cap_table.add_column("Current Price", style="green", width=market_cap_table_width//4)
    market_cap_table.add_column("Market Cap (B USD)", style="magenta", width=market_cap_table_width//4)

    for cap in market_cap:
        market_cap_table.add_row(cap["name"], f"{cap['price']:.4f}$", f"{cap['market_cap'] / 1e9:.2f} B")

    return gainers_table, losers_table, volume_table, market_cap_table

# Function to create layout
def create_layout(gainers_table, losers_table, volume_table, market_cap_table):
    layout = Layout()

    layout.split(
        Layout(name="upper"),
        Layout(name="lower"),
    )

    layout["upper"].split_row(
        Layout(gainers_table, name="gainers"),
        Layout(losers_table, name="losers"),
    )

    layout["lower"].split_row(
        Layout(volume_table, name="volume"),
        Layout(market_cap_table, name="market_cap"),
    )

    return layout

# Main function to run the script
def main():
    console = Console()
    tickers = get_sp500_tickers()
    print("sp500 stock tickers: ", tickers)
    complete_stock_data = get_stock_data(tickers)
    filtered_stock_tickers = get_filtered_stock_tickers(complete_stock_data)
    print("filtered_stock_tickers: ", filtered_stock_tickers)

    with Live(console=console, refresh_per_second=1):
        while True:
            stock_data = get_stock_data(filtered_stock_tickers)
            gainers_table, losers_table, volume_table, market_cap_table = create_tables(stock_data)
            layout = create_layout(gainers_table, losers_table, volume_table, market_cap_table)
            console.print(layout)
            time.sleep(30)

if __name__ == "__main__":
    main()
