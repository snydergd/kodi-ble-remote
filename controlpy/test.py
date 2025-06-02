import asyncio

async def do(val):
    print("Start")
    await asyncio.sleep(5)
    print("Hi " + val)

async def main():
    print("main")
    task = asyncio.create_task(do("stuff"))
    await asyncio.sleep(3)
    task.cancel()
    await asyncio.sleep(3)
    print("All done")

asyncio.run(main())