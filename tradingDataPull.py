import yfinance as yf
import json
import time
from kafka import KafkaProducer
from datetime import datetime

# Initialize Kafka Producer
producer = KafkaProducer(bootstrap_servers=['localhost:9092'], value_serializer=lambda v: json.dumps(v).encode('utf-8'))

# Variable to store the last sent date
last_sent_date = None

def time_until_next_minute():
    """Calculate the number of seconds until the next minute."""
    now = datetime.now()
    # Calculate the number of seconds until the next minute
    seconds_until_next_minute = 60 - now.second
    return seconds_until_next_minute

def fetch_stock_data():
    global last_sent_date  # Use the global variable to track the last sent date
    ticker = 'TSLA'
    
    while True:  # Run the loop indefinitely to keep fetching data at regular intervals
        # Wait until the start of the next minute
        time_to_wait = time_until_next_minute()
        time.sleep(time_to_wait)
        print("Checking yfinance for new data")

        # Download stock data with minute-level intervals for the last day
        stock_data = yf.download(ticker, period="1d", interval="1m")
       

        # Get the most recent row (latest data point)
        latest_row = stock_data.iloc[-1]
        
        # Create the stock dictionary for the most recent data
        stock_dict = {
            'date': latest_row.name.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': ticker,
            'Open': latest_row['Open'].item(),
            'High': latest_row['High'].item(),
            'Low': latest_row['Low'].item(),
            'Close': latest_row['Close'].item(),
            'Volume': latest_row['Volume'].item()
        }

        # Only send data to Kafka if the date has changed
        if last_sent_date is None or stock_dict['date'] != last_sent_date:
            # Sending data to Kafka
            print(f"Sending to Kafka: {stock_dict}")
            producer.send('stock-data-topic', stock_dict)
            producer.flush()  # Make sure the message is sent
            
            # Update the last sent date
            last_sent_date = stock_dict['date']
        
if __name__ == '__main__':
    fetch_stock_data()
