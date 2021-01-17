import logging
from datetime import datetime
import time
import random
conn = __import__('settings').global_conn

def create_table_if_not_exist():
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS water_breaks (id SERIAL PRIMARY KEY, deviceID STRING, date DATE, time INT, quantity INT)")
    conn.commit()

def create_user_table_if_not_exist():
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS users (deviceID STRING PRIMARY KEY, deviceName STRING, timer INT)")
    conn.commit()

def update_time(device_id, device_name, new_time):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE deviceID = '" + device_id + "';"
        )
        row = cur.fetchall()          
    conn.commit()

    if len(row) == 0:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (deviceID, deviceName, timer) VALUES ('" + device_id + "', '" + device_name + "', " + str(new_time) + ");"
            )      
        conn.commit()
    else:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET timer = " + str(new_time) + " WHERE deviceID = '" + device_id + "';"
            )
        conn.commit()
    
    return {"device_id": device_name, "device_name": device_name, "timer": new_time}

def get_user_time(device_id):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM users WHERE deviceid = '" + device_id + "';"
        )
        row = cur.fetchall()

        if len(row) == 0:
            return -1

        time = row[1]
        return time
    conn.commit()

def create_entry(message_id, time_sent, weight):
    with conn.cursor() as cur:
        create_table_if_not_exist()
        quantity = get_quantity(message_id)
        command = "INSERT INTO water_breaks (deviceID, date, time, quantity) VALUES (%s, %s, %s, %s)"
        formatted_date = datetime.now().strftime('%Y-%m-%d')
        formatted_time = datetime.now().strftime('%H:%M:%S')
        cur.execute(command, (message_id, formatted_date, formatted_time, quantity))
        logging.debug("create_entry(): status message: %s", cur.statusmessage)
    conn.commit()

def delete_entries():
    with conn.cursor() as cur:
        cur.execute("DELETE FROM hydronizer.water_breaks")
        logging.debug("delete_entries(): status message: %s", cur.statusmessage)
    conn.commit()

def print_breaks():
    with conn.cursor() as cur:
        cur.execute("SELECT id, time, quantity FROM water_breaks")
        logging.debug("print_breaks(): status message: %s", cur.statusmessage)
        rows = cur.fetchall()
        conn.commit()
        print(f"Breaks at {time.asctime()}:")
        for row in rows:
            print(row)

def get_quantity(device):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM water_breaks WHERE deviceid = '" + device + "' ORDER BY id DESC LIMIT 1;"
        )
        rows = cur.fetchall()
        lastQuantity = int(rows[0][4])
        return lastQuantity - random.randrange(30,51)
    conn.commit()

def get_last_entry(device_id):
    with conn.cursor() as cur:
        command = "SELECT * FROM water_breaks WHERE deviceid = '{}' ORDER BY id DESC LIMIT 1;".format(device_id)
        print(type(command))
        print(command)
        cur.execute(command)
        row = cur.fetchall()[0]

        last_entry = {
            "message_id": row[0],
            "device_id": row[1],
            "date": row[2].strftime("%Y-%m-%d"),
            "time": row[3].strftime("%H:%M:%S"),
            "quantity": row[4]
        }

        print(last_entry)
        print(type(last_entry))
    conn.commit()
    return last_entry

def get_metrics_db(device_id):
    # returns number of sips from today, total water consumed, average, amount of water you need to 
    with conn.cursor() as cur:
        formatted_date = datetime.now().strftime('%Y-%m-%d')
        command = "SELECT * FROM water_breaks WHERE deviceid = '{}' AND date = '{}' ORDER BY time ASC;".format(device_id, formatted_date)
        cur.execute(command)
        data_today = cur.fetchall()
        print(data_today)
        print(type(data_today))
        num = len(data_today)
        print(num)
    conn.commit()

    total_today = 0
    for row in data_today:
        total_today += row[4]
    

    DAILY_RECOMMENDED = 2000
    amount_left = DAILY_RECOMMENDED - total_today
    if amount_left < 0:
        amount_left = 0
    
    with conn.cursor() as cur:
        command = "SELECT * FROM water_breaks WHERE deviceid = '{}';".format(device_id)
        cur.execute(command)
        all_data = cur.fetchall()
        total_consumed = 0
        for row in all_data:
            total_consumed += row[4]
    conn.commit()

    metrics = {
        "number_of_sips": num,
        "total_consumed_today": total_today,
        "total_consumed": total_consumed,
        "amount_left": amount_left
    }

    return metrics