from supabase import create_client
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timezone

def read_last_fetched_data():
    try:
        with open('latest_fetched_data.txt', 'r') as file:
            file_content = file.read().strip()
            if '|' in file_content:
                parts = file_content.split('|')
                if len(parts) == 2:
                    last_date, last_letters = parts[0].strip(), parts[1].strip()
                    return datetime.fromisoformat(last_date).replace(tzinfo=timezone.utc), last_letters
                else:
                    print("File format is incorrect. Expected two parts separated by '|'.")
                    return datetime.min.replace(tzinfo=timezone.utc), ''
            else:
                print("No delimiter found in file. Expected '|'.")
                return datetime.min.replace(tzinfo=timezone.utc), ''
    except FileNotFoundError:
        print("File not found. Starting from the beginning.")
        return datetime.min.replace(tzinfo=timezone.utc), ''

def write_last_fetched_data(date, letters):
    with open('latest_fetched_data.txt', 'w') as file:
        file.write(f"{date.isoformat()}|{letters}")

# Function to write the fetched orders to a file
def write_orders_to_file(orders):
    with open('orders_data.txt', 'a') as file:
        for order in orders:
            file.write(f"{order}\n") 

load_dotenv()
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')

supabase = create_client(supabase_url, supabase_key)

last_fetched_order_date, last_fetched_letters = read_last_fetched_data()

while True:
    try:
        data = supabase.table('order').select('*').gt('order_date', last_fetched_order_date.isoformat()).execute()

        new_rows = data.data
        if new_rows:
            new_last_fetched_date = max(datetime.fromisoformat(row['order_date']) for row in new_rows)
            new_last_fetched_letters = new_rows[-1]['letters']
            print("New data discovered:")
            print(new_rows)
            write_last_fetched_data(new_last_fetched_date, new_last_fetched_letters)
            write_orders_to_file(new_rows)  # Save the new orders to a file

            last_fetched_order_date, last_fetched_letters = new_last_fetched_date, new_last_fetched_letters

            for row in new_rows:
                try:
                    update_response = supabase.table('order').update({'processed': True}).eq('order_id', row['order_id']).execute()
                    if update_response.status_code != 200:  
                        print(f"An error occurred while updating order {row['order_id']}")
                    else:
                        print(f"Order {row['order_id']} marked as processed.")
                except Exception as e:
                    print(f"An error occurred while updating order {row['order_id']}: {e}")

        else:
            print("There is no new data.")

    except Exception as e:
        print(f"An error occurred: {e}")

    time.sleep(1)
