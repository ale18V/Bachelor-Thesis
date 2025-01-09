import asyncio
task: asyncio.Task[None]


async def coroutine_that_will_be_cancelled() -> None:
    print("Running in background")
    while True:
        print("Running in background")
        await asyncio.sleep(1)


async def bar() -> None:
    await asyncio.sleep(2)
    task.cancel()
    print("Cancelled the background task")


async def main() -> None:
    foo = asyncio.create_task(coroutine_that_will_be_cancelled())
    try:
        await foo
    except asyncio.CancelledError:
        print("Task cancelled")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    loop.create_task(bar())
    loop.run_forever()
