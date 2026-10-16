import urllib.request
import json
import asyncio
import sys

# Test reading console logs from CDP page
async def main():
    import websockets
    # find target ws url
    with urllib.request.urlopen("http://127.0.0.1:9222/json") as r:
        pages = json.loads(r.read().decode())
    target = None
    for p in pages:
        if '8080' in p.get('url', ''):
            target = p['webSocketDebuggerUrl']
            break
    print("Connecting to ws:", target)
    async with websockets.connect(target) as ws:
        await ws.send(json.dumps({'id': 1, 'method': 'Console.enable'}))
        await ws.send(json.dumps({'id': 2, 'method': 'Runtime.enable'}))
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': 'console.log("TEST EVAL")'}}))
        
        for _ in range(10):
            msg = await ws.recv()
            data = json.loads(msg)
            if 'Console.messageAdded' in msg or 'Runtime.consoleAPICalled' in msg or 'exceptionThrown' in msg:
                print("LOG/ERR:", data)

if __name__ == '__main__':
    try:
        import websockets
        asyncio.run(main())
    except ImportError:
        print("websockets not installed")
