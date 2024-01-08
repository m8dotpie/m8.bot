import asyncio
import socket
import json
from functools import partial

async def process_log_data(data, callback):
    try:
        # Decode the received data as a JSON string
        log_entry_json = data.decode('utf-8')

        try:
            # Attempt to parse the JSON string into a Python dictionary
            log_entry = json.loads(log_entry_json)

            # Call the callback function with the log entry as an argument
            if callback:
                await callback(log_entry)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Invalid JSON received: {log_entry_json}")
    except Exception as e:
        print(f"Error: {e}")

async def start_log_listener(host, port, callback):
    try:
        server = await asyncio.start_server(
             partial(client_connected, callback=callback), host, port)

        print(f"Listening for logs on {host}:{port}")

        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Error: {e}")

async def client_connected(reader, writer, callback):
    try:
        addr = writer.get_extra_info('peername')
        print(f"Connected by {addr}")

        while True:
            data = await reader.read(1024)
            if not data:
                break

            asyncio.create_task(process_log_data(data, callback))

    except Exception as e:
        print(f"Error: {e}")
