import uvicorn
from aiohttp import web
from starlette.requests import Request
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import JSONResponse
import subprocess
from dotenv import load_dotenv
import os
import signal
from time import sleep

load_dotenv()

PORT = int(os.getenv("GITHUB_WEBHOOK_PORT"))

async def github_webhook(request: Request):
    event = request.headers.get('X-GitHub-Event')
    body = await request.json()
    if event == 'push' and body['ref'] == 'refs/heads/main':
        git_pull()

        return JSONResponse({'message': 'Webhook received and processed.'})

    return JSONResponse({'message': 'Webhook ignored.'})

def git_pull():
    try:
        subprocess.run(['git', 'pull'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git pull failed: {e}")

routes = [
    Route('/', github_webhook, methods=['POST']),
]

app = Starlette(routes=routes)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=PORT)
