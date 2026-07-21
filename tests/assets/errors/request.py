import asyncio
import multiprocessing
import os
import signal
import urllib.error
import urllib.request
from contextlib import asynccontextmanager

from fastapi import FastAPI

POLL_INTERVAL = 0.05
STARTUP_TIMEOUT = 10.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def trigger_request() -> None:
        url = f"http://127.0.0.1:{os.environ['FASTAPI_PORT']}/"
        loop = asyncio.get_running_loop()
        deadline = loop.time() + STARTUP_TIMEOUT
        # Poll until the server answers, so the test runs as soon as it is up
        while True:
            try:
                await asyncio.to_thread(urllib.request.urlopen, url, timeout=2)
            except urllib.error.HTTPError:
                break  # Server is up and answered with the expected 500
            except urllib.error.URLError:
                if loop.time() > deadline:
                    return  # Server never came up; let the test fail on output
            await asyncio.sleep(POLL_INTERVAL)
        # Let uvicorn flush the exception log before shutting down
        await asyncio.sleep(0.2)
        target_pid = (
            os.getpid()
            if multiprocessing.current_process().name == "MainProcess"
            else os.getppid()
        )
        try:
            os.kill(target_pid, signal.SIGTERM)
        except ProcessLookupError:
            pass  # Another worker already terminated the parent

    asyncio.create_task(trigger_request())
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def broken() -> None:
    try:
        {}["missing_key"]
    except KeyError as exc:
        raise RuntimeError("boom from request") from exc
