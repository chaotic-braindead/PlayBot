import pafy
import youtube_dl
with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
    info = ydl.extract_info("https://www.youtube.com/watch?v=ic8j13piAhQ", download=False)
    print(info)
    print(info['formats'][0]['url'])