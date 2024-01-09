import uvicorn
from aiohttp import web
from starlette.requests import Request
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import JSONResponse
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()

PORT = os.getenv("GITHUB_WEBHOOK_PORT")
START_COMMAND = ['python', '-u', 'main.py']

# Store the process ID of the running Python script
running_process = None

async def github_webhook(request: Request):
    event = request.headers.get('X-GitHub-Event')

    if event == 'push' and request['body']['ref'] == 'refs/heads/main']:
        git_pull()
        restart_python_script()

        return JSONResponse({'message': 'Webhook received and processed.'})

    return JSONResponse({'message': 'Webhook ignored.'})

def git_pull():
    try:
        subprocess.run(['git', 'pull'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git pull failed: {e}")

def restart_python_script():
    global running_process
    if running_process is not None:
        # Terminate the running Python script
        try:
            os.kill(running_process.pid, os.SIGTERM)
        except ProcessLookupError:
            pass  # Process has already terminated

    # Start the Python script as a new process
    running_process = subprocess.Popen(START_COMMAND)

routes = [
    Route('/', github_webhook, methods=['POST']),
]

app = Starlette(routes=routes)

if __name__ == '__main__':
    running_process = subprocess.Popen(START_COMMAND)

    uvicorn.run(app, host='0.0.0.0', port=PORT)
