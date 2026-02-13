print("🚀 BOT BAŞLADI!")

import os
import asyncio
import requests
import re
import time
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

async def get_tiktok_data(username):
    print(f"🔍 TikTok kullanıcısı: @{username}")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        # Profil sayfasına git
        profile_url = f"https://www.tiktok.com/@{username}"
        print(f"🌐 Gidilen URL: {profile_url}")
        
        try:
            await page.goto(profile_url, timeout=60000)
            print("✅ Sayfa yüklendi")
        except Exception as e:
            print(f"❌ Sayfa yüklenemedi: {e}")
            await browser.close()
            return None, [], []
        
        # Sayfanın yüklenmesini bekle
        print("⏳ Sayfa yükleniyor...")
        await page.wait_for_timeout(15000)
        
        # ----- PROFİL BİLGİLERİNİ ÇEK -----
        profile_data = {}
        
        # Profil fotoğrafı
        try:
            avatar = await page.eval_on_selector(
                'img[alt*="avatar"], img[src*="avatar"]',
                'el => el.src'
            )
            profile_data['avatar'] = avatar
            print(f"🖼 Profil fotoğrafı bulundu")
        except:
            profile_data['avatar'] = None
            print("⚠️ Profil fotoğrafı bulunamadı")
        
        # Kullanıcı adı ve isim
        try:
            display_name = await page.eval_on_selector(
                'h1[data-e2e="user-title"], h1[class*="share-title"]',
                'el => el.textContent'
            )
            profile_data['display_name'] = display_name.strip() if display_name else username
            print(f"👤 İsim: {profile_data['display_name']}")
        except:
            profile_data['display_name'] = username
        
        # Takipçi sayısı
        try:
            follower_text = await page.eval_on_selector(
                'strong[data-e2e="followers-count"], strong[title*="Takipçi"]',
                'el => el.textContent'
            )
            profile_data['followers'] = follower_text.strip() if follower_text else "0"
            print(f"👥 Takipçi: {profile_data['followers']}")
        except:
            profile_data['followers'] = "Bilinmiyor"
        
        # Takip edilen sayısı
        try:
            following_text = await page.eval_on_selector(
                'strong[data-e2e="following-count"], strong[title*="Takip"]',
                'el => el.textContent'
            )
            profile_data['following'] = following_text.strip() if following_text else "0"
            print(f"👥 Takip edilen: {profile_data['following']}")
        except:
            profile_data['following'] = "Bilinmiyor"
        
        # Biyografi
        try:
            bio = await page.eval_on_selector(
                'h2[data-e2e="user-bio"], div[class*="bio"]',
                'el => el.textContent'
            )
            profile_data['bio'] = bio.strip() if bio else "Biyografi yok"
            print(f"📝 Biyografi: {profile_data['bio'][:50]}...")
        except:
            profile_data['bio'] = "Biyografi yok"
        
        # ----- VİDEO LİNKLERİNİ ÇEK (KENDİ VİDEOLARI) -----
        video_links = []
        
        # Tüm video linklerini topla
        try:
            all_links = await page.eval_on_selector_all(
                'a[href*="/video/"]',
                'els => els.map(el => el.href)'
            )
            print(f"🔗 Bulunan tüm linkler: {len(all_links)}")
            
            # Kendi videoları (profildeki linkler)
            if all_links:
                video_links = list(set(all_links))[:10]
                print(f"🎥 Kendi videoları: {len(video_links)}")
        except Exception as e:
            print(f"⚠️ Video linkleri alınamadı: {e}")
        
        # ----- REPOST LİNKLERİNİ ÇEK (REPOST SAYFASINDAN) -----
       # Repost linklerini topla (sekme tıklama yöntemi)
repost_links = []
try:
    # Profil sayfasında repost sekmesini bul ve tıkla
    print("🔄 Repost sekmesi aranıyor...")
    repost_tab = await page.query_selector('div[data-e2e="repost-tab"]')
    if repost_tab:
        await repost_tab.click()
        print("✅ Repost sekmesine tıklandı")
        await page.wait_for_timeout(8000)  # İçeriğin yüklenmesini bekle
        
        # Sayfayı kaydırarak daha fazla repost yükle
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(2000)
        
        # Repost linklerini topla
        repost_all = await page.eval_on_selector_all(
            'a[href*="/video/"]',
            'els => els.map(el => el.href)'
        )
        repost_links = list(set(repost_all))[:10]
        print(f"🔄 Repost linkleri: {len(repost_links)}")
    else:
        print("⚠️ Repost sekmesi bulunamadı, alternatif URL deneniyor...")
        # Alternatif olarak eski yöntemi dene
        # ... (eski repost URL'leri)
except Exception as e:
    print(f"⚠️ Repost sekmesi hatası: {e}")
def send_profile_to_discord(profile_data, username):
    print("📤 Profil bilgileri Discord'a gönderiliyor...")
    
    embed = {
        "title": f"👤 {profile_data.get('display_name', username)}",
        "url": f"https://www.tiktok.com/@{username}",
        "color": 0x9b59b6,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{username} • Profil Bilgileri"}
    }
    
    if profile_data.get('avatar'):
        embed["thumbnail"] = {"url": profile_data['avatar']}
    
    embed["fields"] = [
        {"name": "👥 Takipçi", "value": profile_data.get('followers', 'Bilinmiyor'), "inline": True},
        {"name": "👥 Takip", "value": profile_data.get('following', 'Bilinmiyor'), "inline": True},
        {"name": "📝 Biyografi", "value": profile_data.get('bio', 'Bilinmiyor')[:100], "inline": False}
    ]
    
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    try:
        response = requests.post(webhook_url, json={"embeds": [embed]})
        print(f"📨 Profil gönderme cevabı: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Profil gönderme hatası: {e}")
        return False

def send_videos_to_discord(video_links, username, video_type="video"):
    """Toplu video gönderimi - her link için ayrı embed (async DEĞIL)"""
    if not video_links:
        print(f"⚠️ Gönderilecek {video_type} linki yok")
        return 0
    
    title = "🎥 Kendi Videoları" if video_type == "video" else "🔄 Repost Videoları"
    color = 0x00ff00 if video_type == "video" else 0xffaa00
    
    print(f"📤 {len(video_links)} {title} gönderiliyor...")
    
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    gonderilen = 0
    
    for link in video_links:
        embed = {
            "title": title,
            "url": link,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"@{username} • {video_type}"}
        }
        
        try:
            response = requests.post(webhook_url, json={"embeds": [embed]})
            if response.status_code in [200, 204]:
                gonderilen += 1
                print(f"✅ Gönderildi: {link[:50]}...")
            else:
                print(f"⚠️ Hata: {response.status_code}")
            time.sleep(1)  # Rate limit koruması - time.sleep kullan (await DEĞIL)
        except Exception as e:
            print(f"❌ Gönderme hatası: {e}")
    
    return gonderilen

async def main():
    username = os.environ["TIKTOK_USER"]
    
    # Daha önce gönderilen videoları takip et
    sent_videos_file = "sent_videos.txt"
    sent_reposts_file = "sent_reposts.txt"
    
    try:
        with open(sent_videos_file, "r") as f:
            sent_videos = set(f.read().splitlines())
        print(f"📁 Daha önce gönderilen video sayısı: {len(sent_videos)}")
    except:
        sent_videos = set()
        print("📁 sent_videos.txt dosyası bulunamadı")
    
    try:
        with open(sent_reposts_file, "r") as f:
            sent_reposts = set(f.read().splitlines())
        print(f"📁 Daha önce gönderilen repost sayısı: {len(sent_reposts)}")
    except:
        sent_reposts = set()
        print("📁 sent_reposts.txt dosyası bulunamadı")
    
    # Profil daha önce gönderildi mi kontrol et
    profile_sent_file = "profile_sent.txt"
    try:
        with open(profile_sent_file, "r") as f:
            profile_sent = f.read().strip() == username
    except:
        profile_sent = False
    
    # TikTok'tan verileri al
    profile_data, video_links, repost_links = await get_tiktok_data(username)
    
    if not profile_data:
        print("❌ Profil verileri alınamadı, işlem iptal.")
        return
    
    # PROFİL GÖNDERME (ilk defa)
    if not profile_sent:
        print("🆕 Profil bilgileri ilk kez gönderiliyor...")
        if send_profile_to_discord(profile_data, username):
            with open(profile_sent_file, "w") as f:
                f.write(username)
            await asyncio.sleep(2)
    else:
        print("⏩ Profil daha önce gönderilmiş.")
    
    # VİDEO GÖNDERME (sadece yeniler)
    print(f"\n📊 İşlenecek video sayısı: {len(video_links)}")
    yeni_videolar = [link for link in video_links if link not in sent_videos]
    
    if yeni_videolar:
        print(f"🆕 {len(yeni_videolar)} yeni video bulundu")
        gonderilen = send_videos_to_discord(yeni_videolar, username, "video")
        
        # Gönderilenleri kaydet
        for link in yeni_videolar:
            sent_videos.add(link)
        
        with open(sent_videos_file, "w") as f:
            f.write("\n".join(sent_videos))
        print(f"✅ {gonderilen} yeni video gönderildi.")
    else:
        print("⏩ Yeni video yok.")
    
    # REPOST GÖNDERME (sadece yeniler)
    print(f"\n📊 İşlenecek repost sayısı: {len(repost_links)}")
    yeni_repostlar = [link for link in repost_links if link not in sent_reposts]
    
    if yeni_repostlar:
        print(f"🆕 {len(yeni_repostlar)} yeni repost bulundu")
        gonderilen = send_videos_to_discord(yeni_repostlar, username, "repost")
        
        # Gönderilenleri kaydet
        for link in yeni_repostlar:
            sent_reposts.add(link)
        
        with open(sent_reposts_file, "w") as f:
            f.write("\n".join(sent_reposts))
        print(f"✅ {gonderilen} yeni repost gönderildi.")
    else:
        print("⏩ Yeni repost yok.")
    
    print("\n✅ Bot çalışması tamamlandı.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
