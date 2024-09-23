import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from typing import Optional
from zoneinfo import ZoneInfo

from twitchAPI.twitch import Twitch
from twitchAPI.helper import first, limit
from twitchAPI.twitch import VideoType

load_dotenv()  # take environment variables from .env.
UTC = ZoneInfo("UTC")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")

app = FastAPI()


# given a timestamp, return in seconds how many seconds ago it was from now
def seconds_ago(timestamp: datetime) -> int:
    return int((datetime.now(tz=UTC) - timestamp).total_seconds())


def sec2hhmmss(seconds: int) -> str:
    """Convert seconds to hh:mm:ss"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse("favicon.ico")


@app.head("/")
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/{channel_name}", response_class=HTMLResponse)
async def get_channel_vod(channel_name: str = "verylocalmelee") -> Optional[str]:
    print(f"Getting VOD for {channel_name}")
    # initialize the twitch instance, this will by default also create a app authentication for you
    twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    # call the API for the data of your twitch user
    # this returns a async generator that can be used to iterate over all results
    # but we are just interested in the first result
    # using the first helper makes this easy.

    user = await first(twitch.get_users(logins=[channel_name]))
    if not user:
        raise HTTPException(status_code=404, detail="Channel Not Found")
    # print the ID of your user or do whatever else you want with it
    current_stream = await first(twitch.get_streams(user_id=user.id))
    if not current_stream:
        raise HTTPException(status_code=404, detail="No Current Stream Found")
    stream_started_at = current_stream.started_at
    videos = []

    async for recent_video in limit(
        twitch.get_videos(user_id=user.id, video_type=VideoType.ARCHIVE), 5
    ):
        videos.append(recent_video)
    for video in sorted(videos, key=lambda x: stream_started_at - x.created_at):
        live_channel_url = f"https://www.twitch.tv/{channel_name}"
        url_no_ts = video.url
        sa = seconds_ago(video.created_at)
        url_with_ts = f"{video.url}?t={sa}s"
        # return html
        output = f"""
        <html>
        <head>
        <title>{channel_name} VOD {video.title}</title>
        </head>
        <body>
        <h1>{channel_name} VOD</h1>
        <p>Live Channel URL: <a href="{live_channel_url}">{live_channel_url}</a></p>
        <br>
        <p>Video Title: {video.title}</p>
        <p>Video VOD URL with timestamp: <a href="{url_with_ts}">{url_with_ts}</a></p>
        <p>Video VOD URL without timestamp: <a href="{url_no_ts}">{url_no_ts}</a></p>
        <p>Titled Timestamp: <a href="{url_with_ts}">{video.title} ({sec2hhmmss(sa)})</a></p>
        <p>Video Duration: {video.duration}</p>
        <p>Video View Count: {video.view_count}</p>
        <p>Video Published At: {video.published_at}</p>
        <p>Video Created At: {video.created_at}</p>
        </body>
        </html>
        """
        return output
    raise HTTPException(status_code=404, detail="Something went wrong. No VODs found.")


"""
stream output:
{'game_id': '16282',
 'game_name': 'Super Smash Bros. Melee',
 'id': '50483770109',
 'is_mature': True,
 'language': 'en',
 'started_at': '2024-02-25T15:34:52+00:00',
 'tag_ids': [],
 'tags': ['badass', 'English'],
 'thumbnail_url': 'https://static-cdn.jtvnw.net/previews-ttv/live_user_mang0-{width}x{height}.jpg',
 'title': 'Full Bloom 2024 - Finals Day ft. mang0 & more - start.gg/fullbloom '
          '- Ult: twitch.tv/houseof3000',
 'type': 'live',
 'user_id': '26551727',
 'user_login': 'mang0',
 'user_name': 'mang0',
 'viewer_count': 8513}

videos output:
{'created_at': '2024-02-25T15:34:57+00:00',
 'description': '',
 'duration': '4h54m35s',
 'id': '2073413015',
 'language': 'en',
 'published_at': '2024-02-25T15:34:57+00:00',
 'stream_id': '50483770109',
 'thumbnail_url': 'https://vod-secure.twitch.tv/_404/404_processing_%{width}x%{height}.png',
 'title': 'Full Bloom 2024 - Finals Day ft. mang0 & more - start.gg/fullbloom '
          '- Ult: twitch.tv/houseof3000',
 'type': 'archive',
 'url': 'https://www.twitch.tv/videos/2073413015',
 'user_id': '26551727',
 'user_login': 'mang0',
 'user_name': 'mang0',
 'view_count': 610,
 'viewable': 'public'}
"""
