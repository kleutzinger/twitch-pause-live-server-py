import os
from datetime import datetime

from dotenv import load_dotenv
from twitchAPI.twitch import Twitch


import asyncio
from zoneinfo import ZoneInfo

from twitchAPI.helper import first, limit
from twitchAPI.twitch import VideoType

load_dotenv()  # take environment variables from .env.
UTC = ZoneInfo("UTC")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")


# given a timestamp, return in seconds how many seconds ago it was from now
def seconds_ago(timestamp: datetime) -> int:
    return int((datetime.now(tz=UTC) - timestamp).total_seconds())


async def get_channel_vod(channel_name: str = "verylocalmelee") -> str:
    # initialize the twitch instance, this will by default also create a app authentication for you
    twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    # call the API for the data of your twitch user
    # this returns a async generator that can be used to iterate over all results
    # but we are just interested in the first result
    # using the first helper makes this easy.
    user = await first(twitch.get_users(logins=[channel_name]))
    if not user:
        return ""
    # print the ID of your user or do whatever else you want with it
    recent_stream = await first(twitch.get_streams(user_id=user.id))
    stream_started_at = recent_stream.started_at
    videos = []

    async for recent_video in limit(
        twitch.get_videos(user_id=user.id, video_type=VideoType.ARCHIVE), 5
    ):
        videos.append(recent_video)
    for video in sorted(videos, key=lambda x: stream_started_at - x.created_at):
        sa = seconds_ago(video.created_at)
        url_with_ts = f"{video.url}?t={sa}s"
        print(video.title, url_with_ts)
        return url_with_ts
    return ""


# run this example
asyncio.run(get_channel_vod())


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
