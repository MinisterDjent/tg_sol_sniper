import asyncio
import websockets
import json
import os
import requests
from dotenv import load_dotenv
from time import sleep

load_dotenv()

logged_snipes = set()

thanatos_main_key = os.getenv('thanatos_main_key').strip()
chat_id = -1002600440989

async def receive_logs():

    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            while True:
                message = await websocket.recv()  # Wait for a message
                logs = json.loads(message)  # Deserialize the JSON string
                await send_logs(logs)  # Send the logs to Telegram
    except Exception as e:
            print(f"Error connecting to local websocket: {e}")

async def send_logs(logs):
    if logs['Address'] not in logged_snipes:
        message = f'''
!!!NEW TOKEN SNIPE!!!
\nName: {logs['Name']}
\nSymbol: {logs["Symbol"]}
\nAddress: {logs['Address']}
\nImage: {logs.get('Token Image', 'N/A')}
\nSolScan: {logs['SolScan']}
\nBirdeye: {logs['Birdeye']}
'''

        send_snipe_url = f'https://api.telegram.org/bot{thanatos_main_key}/sendMessage?chat_id={chat_id}&text={message}'
        response = requests.get(send_snipe_url)
        print(f"Sent latest log. Response: {response.status_code}")
        logged_snipes.add(logs['Address'])
        sleep(7)

async def main():
    try:
        while True:
            await asyncio.gather(receive_logs())
    except Exception as e:
        print(f"Error in main loop: {e}")

if __name__ == '__main__':
    asyncio.run(main())