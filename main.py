#!/usr/bin/python3
from aiohttp import web
from ipaddress import ip_address
import asyncio
import json
import syslog

async def input_validation(ip, begin_port, end_port):
    try:
        ip_address(ip)
    except:
        syslog.syslog(syslog.LOG_ERR, "Invalid IP address")
        return {"error": "Invalid IP address"}

    if (begin_port < 1 or end_port < 1):
        syslog.syslog(syslog.LOG_ERR, "Port value cannot be less than 1.")
        return {"error": "Port value cannot be less than 1."}
    if (begin_port > 65535 or end_port > 65535):
        syslog.syslog(syslog.LOG_ERR, "Port value cannot be higher than 65535.")
        return {"error": "Port value cannot be higher than 65535."}
    if (begin_port > end_port):
        syslog.syslog(syslog.LOG_ERR, "Begin port cannot be higher than End port.")
        return {"error": "Begin port cannot be higher than End port."}
    return ""

async def scanport(ip, port):
    conn = asyncio.open_connection(ip, port)
    try:
        reader, writer = await asyncio.wait_for(conn, timeout=0.5)
        return {port: 'open'}
    except:
        return {port: 'close'}
    finally:
        if 'writer' in locals():
            writer.close()

async def portscanner(ip, begin_port, end_port):
    tasks = [asyncio.ensure_future(scanport(ip, port)) for port in range(begin_port, end_port+1)]
    responses = await asyncio.gather(*tasks)
    return responses

async def handle(request):
    ip = request.match_info.get('ip')
    begin_port = int(request.match_info.get('begin_port'))
    end_port = int(request.match_info.get('end_port'))
    validate_result = await input_validation(ip, begin_port, end_port)
    if not len(validate_result):
        result = await portscanner(ip, begin_port, end_port)
    else:
        result = validate_result
    return web.Response(text=json.dumps(result), status=200)

app = web.Application()
app.router.add_get('/scan/{ip}/{begin_port}/{end_port}', handle)
web.run_app(app)
