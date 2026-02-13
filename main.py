from TikTokApi import TikTokApi
import asyncio
import os
import requests
from datetime import datetime

async def get_reposts_and_videos():
    async with TikTokApi() as api:
        await api.create_sessions(num_sessions=1, headless=True)
        user = api.user(username=os.environ["TIKTOK_USER"])
        
        # Kendi gönderileri
        videos = []
        async for video in user.videos(count=5):
            videos.append(video)
        
        # REPOSTLAR (beğeniler)
        reposts = []
        async for video in user.liked(count=5):
            reposts.append(video)
            
        return videos, reposts

def send_discord(video, is_repost):
    embed = {
        "title": "🔁 Repost" if is_repost else "🎥 Yeni Gönderi",
        "description": video.get("desc", "")[:100],
        "url": f"https://www.tiktok.com/@{os.environ['TIKTOK_USER']}/video/{video['id']}",
        "color": 0xffaa00 if is_repost else 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "thumbnail": {"url": video.get("video", {}).get("cover", "")}
    }
    requests.post(os.environ["DISCORD_WEBHOOK"], json={"embeds": [embed]})

async def main():
    vids, reps = await get_reposts_and_videos()
    for v in vids: send_discord(v, False)
    for r in reps: send_discord(r, True)

if __name__ == "__main__":
    asyncio.run(main())
