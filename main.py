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
        
        # ---- DİREKT REPOST SAYFASINA GİT (en önemli kısım) ----
        repost_url = f"https://www.tiktok.com/@{username}?lang=en"
        print(f"🌐 Gidilen URL: {repost_url}")
        await page.goto(repost_url, timeout=60000)
        await page.wait_for_timeout(10000)  # 10 saniye bekle (sayfanın tam yüklenmesi için)
        
        # Sayfanın yüklendiğine dair kontrol
        print(f"📄 Sayfa başlığı: {await page.title()}")
        
        # Tüm video linklerini bul (daha geniş seçici)
        all_links = await page.eval_on_selector_all(
            'a[href*="/video/"]',
            'els => els.map(el => el.href)'
        )
        print(f"🔗 Bulunan tüm video linkleri: {len(all_links)}")
        
        # Repost'ları ayırmak için sayfa kaynağını kontrol et
        page_content = await page.content()
        if 'repost' in page_content.lower():
            print("✅ Sayfada 'repost' ifadesi bulundu")
        
        # Benzersiz linkleri al, ilk 10'u seç
        unique_links = list(set(all_links))[:10]
        print(f"🎯 Seçilen link sayısı: {len(unique_links)}")
        
        # Repost linkleri (hepsini repost kabul ediyoruz çünkü repost sayfasındayız)
        repost_links = unique_links
        
        # Kendi videoları için ayrıca profil sayfasına gitme (isteğe bağlı)
        # Şimdilik sadece repost'ları alalım
        videos = []
        
        await browser.close()
        return videos, repost_links

def send_to_discord(video_url, is_repost, username):
    print(f"📤 Discord'a gönderiliyor: {video_url}")
    embed = {
        "title": "🔄 Yeni Repost",
        "url": video_url,
        "color": 0xffaa00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{username} • Repost"}
    }
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    try:
        response = requests.post(webhook_url, json={"embeds": [embed]})
        print(f"📨 Discord cevabı: {response.status_code}")
    except Exception as e:
        print(f"❌ Discord gönderme hatası: {e}")

async def main():
    username = os.environ["TIKTOK_USER"]
    
    # Daha önce gönderilenleri takip et
    sent_file = "sent.txt"
    try:
        with open(sent_file, "r") as f:
            sent = set(f.read().splitlines())
        print(f"📁 Daha önce gönderilen link sayısı: {len(sent)}")
    except:
        sent = set()
        print("📁 sent.txt dosyası bulunamadı, yeni oluşturulacak.")
    
    # TikTok'tan verileri al (sadece repost'lar)
    videos, reposts = await get_user_videos_and_reposts(username)
    
    print(f"📊 İşlenecek repost sayısı: {len(reposts)}")
    
    # Repostları kontrol et (videos boş, sadece repost'lar)
    yeni_sayisi = 0
    for r in reposts:
        if r not in sent:
            send_to_discord(r, True, username)
            sent.add(r)
            yeni_sayisi += 1
            await asyncio.sleep(2)  # Discord rate limit koruması
        else:
            print(f"⏩ Daha önce gönderilmiş: {r}")
    
    print(f"✅ {yeni_sayisi} yeni repost gönderildi.")
    
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
