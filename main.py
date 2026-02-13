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

async def get_repost_links(username):
    print(f"🔍 TikTok kullanıcısı: @{username}")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        # Profil sayfasına git
        profile_url = f"https://www.tiktok.com/@{username}"
        print(f"🌐 Gidilen URL: {profile_url}")
        await page.goto(profile_url, timeout=60000)
        
        # Sayfanın yüklenmesini bekle
        print("⏳ Sayfa yükleniyor...")
        await page.wait_for_timeout(15000)
        
        # Tüm video linklerini bul
        all_links = await page.eval_on_selector_all(
            'a[href*="/video/"]',
            'els => els.map(el => el.href)'
        )
        print(f"🔗 Bulunan tüm video linkleri: {len(all_links)}")
        
        # Linkleri yazdır (debug)
        for i, link in enumerate(all_links[:10]):
            print(f"   {i+1}. {link}")
        
        # Benzersiz linkleri al, maksimum 10 tane
        unique_links = list(set(all_links))[:10]
        print(f"🎯 Benzersiz link sayısı: {len(unique_links)}")
        
        await browser.close()
        return unique_links

def send_to_discord(video_url, username):
    print(f"📤 Discord'a gönderiliyor: {video_url}")
    embed = {
        "title": "🔄 TikTok Repost",
        "url": video_url,
        "color": 0xffaa00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{username}"}
    }
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    try:
        response = requests.post(webhook_url, json={"embeds": [embed]})
        print(f"📨 Discord cevabı: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Discord gönderme hatası: {e}")
        return False

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
    
    # Repost linklerini al
    repost_links = await get_repost_links(username)
    
    print(f"📊 İşlenecek repost sayısı: {len(repost_links)}")
    
    # Yeni linkleri bul
    yeni_linkler = []
    for link in repost_links:
        if link not in sent:
            yeni_linkler.append(link)
            print(f"🆕 Yeni link bulundu: {link}")
        else:
            print(f"⏩ Daha önce gönderilmiş: {link}")
    
    print(f"🆕 Toplam yeni link sayısı: {len(yeni_linkler)}")
    
    # Yeni linkleri Discord'a gönder
    gonderilen = 0
    for link in yeni_linkler:
        if send_to_discord(link, username):
            sent.add(link)
            gonderilen += 1
            await asyncio.sleep(2)  # Discord rate limit koruması
    
    print(f"✅ {gonderilen} yeni repost gönderildi.")
    
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
