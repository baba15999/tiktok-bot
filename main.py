print("🚀 BOT BAŞLADI!")

import os
import asyncio
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# ========== DISCORD TEST MESAJI ==========
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    test_embed = {
        "title": "🧪 TEST MESAJI",
        "description": "Bot çalışıyor, webhook aktif.",
        "color": 0x0000ff
    }
    try:
        r = requests.post(webhook_url, json={"embeds": [test_embed]})
        print(f"📨 TEST MESAJI GÖNDERİLDİ: {r.status_code}")
    except Exception as e:
        print(f"❌ TEST MESAJI HATASI: {e}")
else:
    print("❌ DISCORD_WEBHOOK ortam değişkeni bulunamadı!")
# ==========================================

async def get_user_videos_and_reposts(username):
    print(f"🔍 TikTok kullanıcısı: @{username}")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        # ---- KENDİ VİDEOLARI ----
        await page.goto(f"https://www.tiktok.com/@{username}", timeout=60000)
        await page.wait_for_timeout(8000)  # Sayfanın tam yüklenmesi için
        
        video_links = await page.eval_on_selector_all(
            'div[data-e2e="user-post-item"] a[href*="/video/"]',
            'els => els.map(el => el.href)'
        )
        print(f"🎥 Bulunan video linkleri: {len(video_links)}")
        for i, link in enumerate(video_links[:3]):
            print(f"   {i+1}. {link}")
        
        # ---- REPOST VİDEOLARI ----
        await page.goto(f"https://www.tiktok.com/@{username}?lang=en", timeout=60000)
        await page.wait_for_timeout(8000)
        
        repost_links = await page.eval_on_selector_all(
            'div[data-e2e="user-repost-item"] a[href*="/video/"]',
            'els => els.map(el => el.href)'
        )
        print(f"🔄 Bulunan repost linkleri: {len(repost_links)}")
        for i, link in enumerate(repost_links[:3]):
            print(f"   {i+1}. {link}")
        
        await browser.close()
        
        # Tekrarları temizle, ilk 5'le sınırla
        videos = list(set(video_links))[:5]
        reposts = list(set(repost_links))[:5]
        return videos, reposts

def send_to_discord(video_url, is_repost, username):
    print(f"📤 Discord'a gönderiliyor: {video_url} (Repost: {is_repost})")
    embed = {
        "title": "🔄 Yeni Repost" if is_repost else "🎥 Yeni Gönderi",
        "url": video_url,
        "color": 0xffaa00 if is_repost else 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{username} • {'Repost' if is_repost else 'Gönderi'}"}
    }
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    try:
        response = requests.post(webhook_url, json={"embeds": [embed]})
        print(f"📨 Discord cevabı: {response.status_code}")
    except Exception as e:
        print(f"❌ Discord gönderme hatası: {e}")

async def main():
    username = os.environ["TIKTOK_USER"]
    
    # Daha önce gönderilenleri takip et (geçici dosya)
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
        else:
            print(f"⏩ Daha önce gönderilmiş: {v}")
    
    # Repostları kontrol et
    for r in reposts:
        if r not in sent:
            send_to_discord(r, True, username)
            sent.add(r)
        else:
            print(f"⏩ Daha önce gönderilmiş repost: {r}")
    
    # Gönderilenleri dosyaya yaz
    with open(sent_file, "w") as f:
        f.write("\n".join(sent))
    print("✅ Bot çalışması tamamlandı.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
