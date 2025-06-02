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

class PlaybackMenu(menu.Menu):
    def select(self, parent=None):
        if self.is_special_selected():
            super().select()
        else:
            asyncio.create_task(self.commands[self.items[self.selected]]())

    async def playpause(self):
        kodi = await get_kodi()
        await kodi.call_method("Player.PlayPause", playerid = 1)

    async def load_title(self):
        kodi = await get_kodi()
        title = (await kodi.call_method("Player.GetItem", playerid = 1))["item"]["label"]
        print(f"title {title}")
        self.update(title = title)
        self.draw()

    def __init__(self, client, title=None):
        super().__init__(client, title if title else "Now Playing", {
            "Play/Pause": self.playpause,
        })
        if not title:
            asyncio.create_task(self.load_title())

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
        await kodi.call_method("Player.Open", item = {"movieid":movieid})
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
