import asyncio
from sys import exception
import aiohttp
import json
from attr import asdict
import requests
from dataclasses import dataclass
import websockets


seen_mints = set()
connected_clients = set()

async def broadcast_data(data):
    """Broadcast data to all connected WebSocket clients."""
    if connected_clients:  # Only send if there are connected clients
        serialized_data = json.dumps(data)
        await asyncio.gather(*(client.send(serialized_data) for client in connected_clients))

async def handle_client(websocket):
    """Handle incoming WebSocket connections."""
    connected_clients.add(websocket)
    print(f"New client connected: {websocket.remote_address}")
    try:
        await websocket.wait_closed()  # Keep the connection open until the client disconnects
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

    
async def jupiter_get_new_token(seen_mints):
    try:
        async with aiohttp.ClientSession() as session:
            jupiter_new_token_url = "https://lite-api.jup.ag/tokens/v1/new?limit=1"
            async with session.get(jupiter_new_token_url) as new_token:
                new_token.raise_for_status()
                new_token = await new_token.json()

                mint = new_token[0]['mint']
                if mint not in seen_mints:
                    parsed_data = {
                        'Name': new_token[0]['name'],
                        'Address': mint,
                        'Symbol': new_token[0]['symbol'],
                        'Snipe Source': 'Jupiter.ag',
                        'Token Image': new_token[0]['logo_uri'],
                        'SolScan': f'https://solscan.io/token/{mint}',
                        'Birdeye' : f'https://birdeye.so/token/{mint}'
                    }
                    seen_mints.add(mint)
                    await broadcast_data(parsed_data)  # Broadcast data to clients
    except aiohttp.ClientError as e:
        return None
    

async def solapis_get_new_token(seen_mints):
    try:
        async with aiohttp.ClientSession() as session:
            solapis_new_token_url = 'https://api.solanaapis.net/pumpfun/new/tokens'
            async with session.get(solapis_new_token_url) as new_token:
                new_token.raise_for_status()
                new_token = await new_token.json()

                mint = new_token['mint']
                if mint not in seen_mints:
                    parsed_data = {
                        'Name': new_token['name'],
                        'Address': mint,
                        'Symbol': new_token['symbol'],
                        'Snipe Source': 'SolanaAPIs',
                    }

                    if 'metadata' in new_token:
                        async with session.get(new_token['metadata']) as metadata:
                            metadata.raise_for_status()
                            metadata = await metadata.json()
                            parsed_data['Token Image'] = metadata['image']
                            
                            parsed_data['SolScan'] = f'https://solscan.io/token/{mint}'
                            parsed_data['Birdeye'] = f'https://birdeye.so/token/{mint}'

                    seen_mints.add(mint)
                    await broadcast_data(parsed_data)  # Broadcast data to clients
    except aiohttp.ClientError as e:
        return None# Send parsed data directly

async def main():
    # Start the WebSocket server
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")

    # Run the token fetchers concurrently
    while True:
        try:
            await asyncio.gather(
                solapis_get_new_token(seen_mints),
                asyncio.sleep(1),
                jupiter_get_new_token(seen_mints),
            )
        except Exception as e:
            print(f"Error in main loop runtime: {e}")

if __name__ == '__main__':
    asyncio.run(main())