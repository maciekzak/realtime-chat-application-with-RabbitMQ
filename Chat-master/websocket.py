import sys
import asyncio
import aio_pika
import websockets

async def keepalive(websocket):
    try:
        await websocket.recv()
    except websockets.ConnectionClosedError as error:
        print(error)
        sys.exit(1)  # Force the script to exit

async def consume(channel, queue_name, websocket):
    async with channel.consume(queue_name) as queue:
        async for message in queue:
            try:
                await websocket.send(message.body.decode())
                message.ack()
            except websockets.ConnectionClosedError as error:
                print(error)
                sys.exit(1)  # Force the script to exit

async def application(websocket, path):
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()

        exchange = path.replace('/', '')
        await channel.set_qos(prefetch_count=1)
        await channel.declare_exchange(exchange, aio_pika.ExchangeType.FANOUT)

        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange)

        # Start the keepalive task
        asyncio.create_task(keepalive(websocket))

        # Consume messages
        await consume(channel, queue.name, websocket)

start_server = websockets.serve(application, 'localhost', 8000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()