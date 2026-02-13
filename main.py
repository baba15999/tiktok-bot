print("🚀 BOT BAŞLADI!")

import os
import asyncio
import requests
import re
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
        
        # Sayfayı yükle (hata yönetimi ile)
        try:
            await page.goto(profile_url, timeout=60000)
            print("✅ Sayfa yüklendi")
        except Exception as e:
            print(f"❌ Sayfa yüklenemedi: {e}")
            await browser.close()
            return None, [], None, None, None
        
        # Sayfanın yüklenmesini bekle (değişken süre)
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
            print(f"🖼 Profil fotoğrafı: {avatar[:50]}...")
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
        
        # ----- VİDEO LİNKLERİNİ ÇEK -----
        video_links = []
        
        # Yöntem 1: Standart seçici
        try:
            links = await page.eval_on_selector_all(
                'a[href*="/video/"]',
                'els => els.map(el => el.href)'
            )
            video_links.extend(links)
            print(f"🔗 Yöntem 1 ile bulunan linkler: {len(links)}")
        except:
            print("⚠️ Yöntem 1 başarısız")
        
        # Yöntem 2: Sayfa kaynağından regex ile bul
        if len(video_links) < 3:
            try:
                content = await page.content()
                video_ids = re.findall(r'/video/(\d+)', content)
                unique_ids = list(set(video_ids))[:10]
                links_from_regex = [f"https://www.tiktok.com/@{username}/video/{vid}" for vid in unique_ids]
                video_links.extend(links_from_regex)
                print(f"🔗 Yöntem 2 ile bulunan linkler: {len(links_from_regex)}")
            except Exception as e:
                print(f"⚠️ Yöntem 2 başarısız: {e}")
        
        # Yöntem 3: Sayfayı kaydır (daha fazla video yükle)
        if len(video_links) < 3:
            try:
                print("📜 Sayfa kaydırılıyor...")
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(3000)
                
                links = await page.eval_on_selector_all(
                    'a[href*="/video/"]',
                    'els => els.map(el => el.href)'
                )
                video_links.extend(links)
                print(f"🔗 Yöntem 3 ile bulunan linkler: {len(links)}")
            except Exception as e:
                print(f"⚠️ Yöntem 3 başarısız: {e}")
        
        # Benzersiz linkleri al, maksimum 10 tane
        unique_links = list(set(video_links))[:10]
        print(f"🎯 Toplam benzersiz link sayısı: {len(unique_links)}")
        
        # Linkleri yazdır
        for i, link in enumerate(unique_links):
            print(f"   {i+1}. {link}")
        
        await browser.close()
        return profile_data, unique_links

def send_profile_to_discord(profile_data, username):
    print("📤 Profil bilgileri Discord'a gönderiliyor...")
    
    embed = {
        "title": f"👤 {profile_data.get('display_name', username)}",
        "url": f"https://www.tiktok.com/@{username}",
        "color": 0xffaa00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{username}"}
    }
    
    # Profil fotoğrafı varsa ekle
    if profile_data.get('avatar'):
        embed["thumbnail"] = {"url": profile_data['avatar']}
    
    # İstatistikleri ekle
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

def send_video_to_discord(video_url, username):
    print(f"📤 Video Discord'a gönderiliyor: {video_url}")
    embed = {
        "title": "🎥 TikTok Videosu",
        "url": video_url,
        "color": 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{username}"}
    }
    
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    try:
        response = requests.post(webhook_url, json={"embeds": [embed]})
        print(f"📨 Video gönderme cevabı: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Video gönderme hatası: {e}")
        return False

async def main():
    username = os.environ["TIKTOK_USER"]
    
    # Daha önce gönderilen videoları takip et
    sent_file = "sent_videos.txt"
    try:
        with open(sent_file, "r") as f:
            sent = set(f.read().splitlines())
        print(f"📁 Daha önce gönderilen video sayısı: {len(sent)}")
    except:
        sent = set()
        print("📁 sent_videos.txt dosyası bulunamadı, yeni oluşturulacak.")
    
    # Profil daha önce gönderildi mi kontrol et
    profile_sent_file = "profile_sent.txt"
    try:
        with open(profile_sent_file, "r") as f:
            profile_sent = f.read().strip() == username
    except:
        profile_sent = False
    
    # TikTok'tan verileri al
    profile_data, video_links = await get_tiktok_data(username)
    
    if not profile_data:
        print("❌ Profil verileri alınamadı, işlem iptal.")
        return
    
    # Profil bilgilerini gönder (ilk defa)
    if not profile_sent:
        print("🆕 Profil bilgileri ilk kez gönderiliyor...")
        if send_profile_to_discord(profile_data, username):
            with open(profile_sent_file, "w") as f:
                f.write(username)
    else:
        print("⏩ Profil daha önce gönderilmiş.")
    
    print(f"📊 İşlenecek video sayısı: {len(video_links)}")
    
    # Yeni videoları bul
    yeni_videolar = []
    for link in video_links:
        if link not in sent:
            yeni_videolar.append(link)
            print(f"🆕 Yeni video bulundu: {link}")
        else:
            print(f"⏩ Daha önce gönderilmiş video: {link}")
    
    print(f"🆕 Toplam yeni video sayısı: {len(yeni_videolar)}")
    
    # Yeni videoları Discord'a gönder
    gonderilen = 0
    for link in yeni_videolar:
        if send_video_to_discord(link, username):
            sent.add(link)
            gonderilen += 1
            await asyncio.sleep(2)  # Discord rate limit koruması
    
    print(f"✅ {gonderilen} yeni video gönderildi.")
    
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
