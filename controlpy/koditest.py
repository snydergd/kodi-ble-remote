from pykodi import Kodi, get_kodi_connection
import asyncio

async def main():
    kc = get_kodi_connection('localhost', 8080, 9090, 'kodi', 'kodi')
    await kc.connect()
    kodi = Kodi(kc)

    for movie in (await kodi.call_method("VideoLibrary.GetMovies"))["movies"]:
        print(movie)

    print(await kodi.call_method("Player.GetPlayers"))
    #print(await kodi.call_method("Player.PlayPause", playerid = 1))
    print(await kodi.call_method("Player.GetActivePlayers"))
    print(await kodi.call_method("Player.GetItem", playerid = 1))
    print(await kodi.call_method("Player.GetProperties", playerid = 1, properties = ["speed"]))
    resumepos = await kodi.call_method("VideoLibrary.GetMovieDetails", movieid = 43, properties = ["resume"])
    print(resumepos)
    await kodi.call_method("Player.Open", item = {"movieid":43}, options = {"resume": True})


asyncio.run(main())