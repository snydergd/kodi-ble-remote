import menu
from pykodi import Kodi, get_kodi_connection
import asyncio

_kodi = None
async def get_kodi():
    global _kodi
    if not _kodi:
        kc = get_kodi_connection('localhost', 8080, 9090, 'kodi', 'kodi')
        await kc.connect()
        _kodi = Kodi(kc)
    return _kodi

INITIAL_TITLE = "Now playing"
class PlaybackMenu(menu.Menu):
    def select(self, parent=None):
        if self.is_special_selected():
            super().select()
        else:
            asyncio.create_task(self.commands[self.items[self.selected]]())

    async def playpause(self):
        await self.load_title(redraw=False)

        kodi = await get_kodi()
        active_players = await kodi.call_method("Player.GetActivePlayers")

        if len(active_players) == 0:
            await kodi.call_method("Player.Open", item = {movieid: self.item['movieid']})
        else:
            await kodi.call_method("Player.PlayPause", playerid = 1)

        await self.load_title()

    async def restart(self):
        kodi = await get_kodi()
        await kodi.call_method("Player.Seek", value={"percentage": 0}, playerid=1)

    async def check_playing(self):
        kodi = await get_kodi()
        speed = (await kodi.call_method("Player.GetProperties", playerid = 1, properties = ["speed"]))["speed"]
        if speed > 0:
            self.playing = True
        else:
            self.playing = False

    async def load_title(self, title=None, redraw=True):
        kodi = await get_kodi()
        if not title or title == INITIAL_TITLE:
            item = (await kodi.call_method("Player.GetItem", playerid = 1))["item"]
            self.item = item
            title = item["label"]
        print(f"title {title}")

        await self.check_playing()
        if not title:
            title = "Nothing playing"
            commands = {}
        else:
            if self.playing:
                commands = {
                    "Pause": self.playpause
                }
            else:
                commands = {
                    "Play": self.playpause
                }

            commands["Restart"] = self.restart

        self.update(title = title, commands=commands)
        if redraw:
            self.draw()

    def __init__(self, client, title=INITIAL_TITLE):
        super().__init__(client, title, {})
        asyncio.create_task(self.load_title(title))

class MovieMenu(menu.Menu):
    async def load_menu(self):
        print("Loading movies")
        kodi = await get_kodi()
        movies = (await kodi.call_method("VideoLibrary.GetMovies"))["movies"]
        self.movies = movies
        commands = {movie["label"]: movie["movieid"] for movie in movies}
        self.update(commands = commands)

    async def play(self, movieid):
        kodi = await get_kodi()
        await kodi.call_method("Player.Open", item = {"movieid":movieid}, options={"resume": True})
        title = [x for x in self.movies if x["movieid"] == movieid][0]["label"]
        print(f"Going to title {title}")
        self.parent.start_delegating(PlaybackMenu(self.client, title=title))

    def select(self, parent=None):
        if self.is_special_selected():
            super().select()
        else:
            asyncio.create_task(self.play(self.commands[self.items[self.selected]]))
    
    def __init__(self, client):
        super().__init__(client, "Movies")
        asyncio.create_task(self.load_menu())


class SystemMenu(menu.Menu):
    async def shutdown(self):
        self.clear()
        kodi = await get_kodi()
        await kodi.call_method("System.Shutdown")

    def __init__(self, client):
        super().__init__(client, "System", {
            "Shutdown": lambda: asyncio.create_task(self.shutdown()),
        })
