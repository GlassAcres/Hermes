from fastapi import Request, Response
from utils.logger import log_debug_deep
import time
import json
import asyncio

async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Read and log the request details
    request_body = b""
    if request.method != "GET":
        request_body = await request.body()

    try:
        request_json = json.loads(request_body.decode('utf-8'))
    except json.JSONDecodeError:
        request_json = "Unable to decode JSON"

    log_debug_deep(f"Request: {request.method} {request.url} Body: {request_json}")

    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    # Assemble response for logging
    response_body = b''
    async for chunk in response.body_iterator:
        response_body += chunk

    try:
        response_json = json.loads(response_body.decode('utf-8'))
    except json.JSONDecodeError:
        response_json = "Unable to decode JSON"

    log_debug_deep(f"Response: Status {response.status_code} Body: {response_json} Duration: {process_time}ms")

    # Create a new response with the same body
    new_response = Response(content=response_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    return new_response
