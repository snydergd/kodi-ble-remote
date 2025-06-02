
from ble_serial.bluetooth.ble_client import BLE_client
import time
import asyncio
import pygame
import numpy as np
import math
import traceback
import signal
import os

from menu import Menu, UI
from kodimenus import MovieMenu, PlaybackMenu, SystemMenu

WHITE=(255,255,255)
BLACK=(0,0,0)

pygame.init()

class ClickPatterns:
    timer: asyncio.Task | None
    def __init__(self, timeout, pattern_callback):
        self.timer = None
        self.timeout = timeout
        self.pattern_callback = pattern_callback
        self.clicks = []
    
    def timeout_handler(self, future):
        clicks = self.clicks
        self.timer = None
        print(f"clicks {clicks}")
        self.clicks = []
        if clicks:
            self.pattern_callback(clicks)

    def click(self):
        print("a")
        if self.timer:
            self.timer.cancel()
        self.clicks.append(time.time())
        self.timer = asyncio.get_running_loop().create_task(asyncio.sleep(self.timeout)).add_done_callback(self.timeout_handler)

class MyClient:
    menu: Menu
    ui: UI
    client: BLE_client
    done: asyncio.Semaphore
    lastclick: int
    lastdown: int
    counter: int
    sendlock: asyncio.Lock
    clickpatterns: ClickPatterns

    def handle_click_pattern(self, pattern):
        if len(pattern) == 2:
            print("Double")
            self.ui.up()
        if len(pattern) == 3:
            self.ui.back()
        elif len(pattern) == 1:
            print("Single")
            self.ui.down()

    @classmethod
    async def create(cls):
        print("Start")
        self = cls()

        self.client = BLE_client(None)
        print("Sleep")
        await asyncio.sleep(2)
        print("Connect")
        await self.client.connect("78:21:84:99:62:C6", None, None, None)
        print("Connected")
        self.client.set_receiver(self._handle)
        print("Setup Characteristics")
        await self.client.setup_chars("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", "6E400003-B5A3-F393-E0A9-E50E24DCCA9E", "rw", True)
        print("Setup done")
    
        self.lastclick = 0
        self.clicks_in_limit = 0
        self.lastdown = 0
        self.done = asyncio.Semaphore(0)
        self.counter = 0
        self.sendlock = asyncio.Lock()

        self.ui = Menu(self.client, "Main", {
            "Now Playing": lambda: PlaybackMenu(self.client),
            "Movies": MovieMenu(self.client),
            "System": SystemMenu(self.client),
        }, self.done.release)
        self.clickpatterns = ClickPatterns(0.4, self.handle_click_pattern)

        old_queue_function = self.client.queue_send
        def replacement(*args, **kwargs):
            if self.done.locked():
                return old_queue_function(*args, **kwargs)
            else:
                return
        self.client.queue_send = replacement
        return self

    def _handle(self, data):
        #print(data)
        async def actual(self, data):
            client = self.client
            now = time.time_ns()

            if data[0] == ord('u'): #backwards - this is down
                self.lastdown = now
            elif data[0] == ord('d'): # backwards - this is up
                if now - self.lastdown > 1000000000:
                    print("Back")
                    self.ui.back()
                elif now - self.lastdown > 400000000:
                    print("Up")
                    self.ui.up()
                elif now - self.lastdown > 200000000:
                    print("Long click")
                    self.ui.select()
                else:
                    self.ui.down()
                    #self.clickpatterns.click()
                # elif now - self.lastclick < 500000000:
                #     self.lastclick = now
                #     print("Heyo")
                #     self.counter -= 2
                #     #await self.drawCircle(20, str(self.counter))
                #     # client.queue_send(b"C")
                #     # client.queue_send(f"S20 20 {self.counter}".encode())
                #     # client.queue_send(b"D")
                #     self.ui.select()
                # else:
                #     self.lastclick = now
                #     self.counter += 1
                #     # await self.drawCircle(20, str(self.counter))
                #     # client.queue_send(b"C")
                #     # client.queue_send(f"S20 20 {self.counter}".encode())
                #     # client.queue_send(b"D")
                #     def finish():
                #         if self.clicks_in_limit
                #     asyncio.get_running_loop().create_task(asyncio.sleep(0.5)).add_done_callback(finish)
                #     self.ui.down()
        future = asyncio.run_coroutine_threadsafe(actual(self, data), asyncio.get_running_loop())
        def handle_future(future):
            exc = future.exception()
            if exc:
                traceback.print_exception(exc)
        future.add_done_callback(handle_future)
    
    async def send_picture(self, x, y, data_to_send):
        client = self.client
        width = len(data_to_send)
        height = len(data_to_send[0])
        LIMIT=128

        print(f"{width}x{height}")
        if width > LIMIT or height > LIMIT:
            for chunkx in range(0, width, LIMIT):
                for chunky in range(0, height, LIMIT):
                    chunk = [[data_to_send[x][y] for y in range(chunky, min(chunky+LIMIT, height))] for x in range(chunkx, min(chunkx+LIMIT, width))]
                    await send_picture(client, x+chunkx, y+chunky, chunk)
        else:
            data = [0 for i in range(width*height)]
            for col in range(width):
                for row in range(height):
                    if data_to_send[col][row]:
                        data[col*8+row//8] |= 1<<(row%8)
            async with self.sendlock:
                client.queue_send(f"P{x} {y} {width} {height} ".encode() + bytes(data))
                client.queue_send(b"D")
                while not client._send_queue.empty():
                    await asyncio.sleep(0)

    async def drawCircle(self, x, text="George"):
        surface = pygame.Surface((128, 64))

        # draw some things
        surface.fill(BLACK)
        pygame.draw.circle(surface, (255, 255, 255), (0, 0), 30)
        pygame.draw.arc(surface, WHITE, pygame.Rect(0, 0, 128, 64), 0, 360)
        font = pygame.font.Font('freesansbold.ttf', 20)
        text = font.render(text, True, WHITE, BLACK)
        textRect = text.get_rect()
        textRect.top = 20
        textRect.left = 10+x
        surface.blit(text, textRect)

        rgb = pygame.surfarray.array3d(surface)
        binary = np.where(rgb.sum(axis=2) > 0, 1, 0)
        bitmap = binary.tolist()

        print("Writing picture")
        await self.send_picture(0, 0, bitmap)

    async def shutdown(self):
        print("Shutting down")
        self.client.queue_send(b"C")
        self.client.queue_send(b"D")
        while not self.client._send_queue.empty():
            await asyncio.sleep(0)
        self.done.release()

    async def run(self):
        client = self.client
        
        main_tasks = {
            asyncio.create_task(client.send_loop()),
            asyncio.create_task(client.check_loop())
        }

        # print("Writing hello world")
        # client.queue_send(b"C")
        # client.queue_send(b"S20 20 Hello World")
        self.ui.draw()

        # client.queue_send(b"S20 30 Welcome to the simulation")

        # length = 4
        # angle = 0
        # for i in range(30):
        #     client.queue_send(f"L10 10 {int(10+length*math.cos(angle))} {int(10+length*math.sin(angle))}".encode())
        #     client.queue_send(b"D")
        #     await asyncio.sleep(0.5)
        #     angle += 2*math.pi/30
        #     if angle > 2*math.pi:
        #         angle -= 2*math.pi
        #         length += 2

        # for i in range(10):
        #     print(f"Writing circle {i}")
        #     await self.drawCircle(i*3, text="George")
        # await asyncio.sleep(10)

        # print("Clearing")
        # client.queue_send(b"C")
        client.queue_send(b"D")

        print("Waiting for done")
        await self.done.acquire()
        client.queue_send(b"C")
        client.queue_send(b"D")
        while not client._send_queue.empty():
            await asyncio.sleep(0)
        print("Disconnect")
        await client.disconnect()
        print("Disconnect done")

        done, pending = await asyncio.wait(main_tasks, return_when=asyncio.FIRST_COMPLETED)

def main():
    print(os.getpid())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    myClient = loop.run_until_complete(MyClient.create())
    print(f"Client {myClient}")
    def shutdown(signum, frame):
        print("I'm here")
        loop.create_task(myClient.shutdown())
    signal.signal(signal.SIGTERM, shutdown)
    loop.run_until_complete(myClient.run())

if __name__ == "__main__":
    main()
