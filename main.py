#!/usr/bin/python3

import asyncio
import json
import logging
import pytest
from aiohttp import web
from ipaddress import ip_address

def input_validation(ip: str, begin_port: int, end_port: int) -> dict:
    try:
        ip_address(ip)
    except ValueError:
        logging.warning("Invalid IP address")
        return {"error": "Invalid IP address"}

    try:
        begin_port = int(begin_port)
    except ValueError:
        logging.warning("begin_port must be integer.")
        return {"error": "begin_port must be integer."}

    try:
        end_port = int(end_port)
    except ValueError:
        logging.warning("end_port must be integer.")
        return {"error": "end_port must be integer."}

    if (begin_port < 1 or end_port < 1):
        logging.warning("Port value cannot be less than 1.")
        return {"error": "Port value cannot be less than 1."}
    if (begin_port > 65535 or end_port > 65535):
        logging.warning("Port value cannot be higher than 65535.")
        return {"error": "Port value cannot be higher than 65535."}
    if (begin_port > end_port):
        logging.warning("Begin port cannot be higher than End port.")
        return {"error": "Begin port cannot be higher than End port."}
    return {"success": "noerror"}

async def portscan(ip: str, port: int) -> dict:
    conn = asyncio.open_connection(ip, port)
    try:
        reader, writer = await asyncio.wait_for(conn, timeout=0.5)
        return {'port': port, 'state': 'open'}
        writer.close()
    except asyncio.TimeoutError:
        return {'port': port, 'state': 'close'}

async def port_range_scan(ip: str, begin_port: int, end_port: int) -> dict:
    tasks = [asyncio.ensure_future(portscan(ip, port)) for port in range(begin_port, end_port+1)]
    responses = await asyncio.gather(*tasks)
    return responses

async def handle(request) -> web.Response:
    ip = request.match_info.get('ip')
    begin_port = request.match_info.get('begin_port')
    end_port = request.match_info.get('end_port')
    validate_result = input_validation(ip, begin_port, end_port)
    if 'error' in validate_result:
        result = validate_result
    else:
        result = await port_range_scan(ip, int(begin_port), int(end_port))
    return web.json_response(result)

def create_app():
    app = web.Application()
    app.router.add_get('/scan/{ip}/{begin_port}/{end_port}', handle)
    return app

async def test_handle(aiohttp_client):
    result = '{"port": 80, "state": "close"}, {"port": 81, "state": "close"}, {"port": 82, "state": "close"}, {"port": 83, "state": "close"}, {"port": 84, "state": "close"}, {"port": 85, "state": "close"}'
    client = await aiohttp_client(create_app())
    resp = await client.get("/scan/192.168.88.100/80/85")
    assert resp.status == 200
    text = await resp.text()
    assert result in text

if __name__ == '__main__':
    web.run_app(create_app())
