print("🚀 BOT BAŞLADI!")
import os
import asyncio
import requests
from datetime import datetime
from playwright.async_api import async_playwright

async def get_user_videos_and_reposts(username):
    async with async_playwright() as p:
        # Firefox kullan, daha az engel
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        # Ana profil – kendi videoları
        await page.goto(f"https://www.tiktok.com/@{username}", timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Video linklerini topla (kendi gönderileri)
        video_links = await page.eval_on_selector_all(
            'a[href*="/video/"]',
            'els => els.map(el => el.href)'
        )
        
        # REPOST SEKMEŞİ – direkt repost sayfasına git
        repost_url = f"https://www.tiktok.com/@{username}?lang=en&is_copy_url=1&is_from_webapp=v1#repost"
        await page.goto(repost_url, timeout=60000)
        await page.wait_for_timeout(5000)
        
        # Repost edilmiş video linklerini topla
        repost_links = await page.eval_on_selector_all(
            'a[href*="/video/"]',
            'els => els.map(el => el.href)'
        )
        
        await browser.close()
        
        # Tekrarları temizle, ilk 5'le sınırla
        videos = list(set(video_links))[:5]
        reposts = list(set(repost_links))[:5]
        
        return videos, reposts

def send_to_discord(video_url, is_repost, username):
    embed = {
        "title": "🔄 Yeni Repost" if is_repost else "🎥 Yeni Gönderi",
        "url": video_url,
        "color": 0xffaa00 if is_repost else 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{username} • {'Repost' if is_repost else 'Gönderi'}"}
    }
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    requests.post(webhook_url, json={"embeds": [embed]})

async def main():
    username = os.environ["TIKTOK_USER"]
    
    # Daha önce gönderilen videoları takip et
    sent_file = "sent.txt"
    try:
        with open(sent_file, "r") as f:
            sent = set(f.read().splitlines())
    except:
        sent = set()
    
    # TikTok'tan verileri al
    videos, reposts = await get_user_videos_and_reposts(username)
    
    # Kendi gönderilerini kontrol et
    for v in videos:
        if v not in sent:
            send_to_discord(v, False, username)
            sent.add(v)
    
    # REPOSTLARI kontrol et
    for r in reposts:
        if r not in sent:
            send_to_discord(r, True, username)
            sent.add(r)
    
    # Gönderilenleri dosyaya yaz
    with open(sent_file, "w") as f:
        f.write("\n".join(sent))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
