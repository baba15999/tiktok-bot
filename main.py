async def get_reposts_and_videos():
    async with TikTokApi() as api:
        # ⚠️ ŞU SATIRI DEĞİŞTİR:
        await api.create_sessions(
            num_sessions=1, 
            headless=True, 
            browser='webkit',        # Chromium yerine WebKit dene
            sleep_after=3           # Her işlemden sonra 3 saniye bekle
        )
        
        user = api.user(username=os.environ["TIKTOK_USER"])
        user_data = await user.info()
        user_id = user_data["user"]["id"]
        
        # Kendi gönderileri - sayıyı 3'e düşür, daha az şüpheli
        videos = []
        async for video in user.videos(count=3):
            videos.append(video)
            await asyncio.sleep(1)   # Her video arasında bekle
        
        # Repost'lar - beğeniler
        reposts = []
        async for video in user.liked(count=3):
            reposts.append(video)
            await asyncio.sleep(1)
            
        return videos, reposts
