import asyncio
import multiprocessing
import os
import signal
import urllib.error
import urllib.request
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def trigger_request() -> None:
        url = f"http://127.0.0.1:{os.environ['FASTAPI_PORT']}/"

        await asyncio.sleep(0.1)
        try:
            await asyncio.to_thread(urllib.request.urlopen, url, timeout=0.5)
        except urllib.error.HTTPError:
            pass

        target_pid = (
            os.getpid()
            if multiprocessing.current_process().name == "MainProcess"
            else os.getppid()
        )
        os.kill(target_pid, signal.SIGTERM)

    asyncio.create_task(trigger_request())
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def broken() -> None:
    try:
        {}["missing_key"]
    except KeyError as exc:
        raise RuntimeError("boom from request") from exc
