print("🚀 BOT BAŞLADI!")

import os
import asyncio
import requests
import re
import time
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from fuzzywuzzy import fuzz

# Opsiyonel: playwright-stealth (kurulu değilse sorun değil)
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except:
    STEALTH_AVAILABLE = False
    print("⚠️ playwright-stealth kurulu değil, devam ediliyor.")

# ========== ORTAM DEĞİŞKENLERİ ==========
webhook_url = os.environ.get("DISCORD_WEBHOOK")
tiktok_user = os.environ.get("TIKTOK_USER")

if not webhook_url or not tiktok_user:
    print("❌ DISCORD_WEBHOOK veya TIKTOK_USER eksik!")
    exit(1)

# ========== TEST MESAJI ==========
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

# ========== FONKSİYONLAR ==========

async def get_tiktok_data(username):
    print(f"🔍 TikTok kullanıcısı: @{username}")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        if STEALTH_AVAILABLE:
            await stealth_async(page)
            print("🕵️ Stealth aktif.")
        
        profile_url = f"https://www.tiktok.com/@{username}"
        print(f"🌐 Gidilen URL: {profile_url}")
        try:
            await page.goto(profile_url, timeout=60000)
            print("✅ Sayfa yüklendi")
        except Exception as e:
            print(f"❌ Sayfa yüklenemedi: {e}")
            await browser.close()
            return None, [], []
        
        await page.wait_for_timeout(20000)
        
        # ----- PROFİL BİLGİLERİ -----
        profile_data = {}
        
        # Avatar
        avatar_selectors = [
            'img[src*="avt"]',
            'img[alt*="avatar"]',
            'img[class*="avatar"]',
            'img[data-e2e="user-avatar"]',
            'img[src*="tiktokcdn.com/avt"]'
        ]
        avatar = None
        for sel in avatar_selectors:
            try:
                avatar = await page.eval_on_selector(sel, 'el => el.src')
                if avatar:
                    print(f"🖼 Avatar bulundu (seçici: {sel})")
                    break
            except:
                continue
        profile_data['avatar'] = avatar
        
        # İsim
        try:
            display_name = await page.eval_on_selector(
                'h1[data-e2e="user-title"], h1[class*="share-title"]',
                'el => el.textContent'
            )
            profile_data['display_name'] = display_name.strip() if display_name else username
        except:
            profile_data['display_name'] = username
        print(f"👤 İsim: {profile_data['display_name']}")
        
        # Takipçi
        try:
            follower_text = await page.eval_on_selector(
                'strong[data-e2e="followers-count"], strong[title*="Takipçi"]',
                'el => el.textContent'
            )
            profile_data['followers'] = follower_text.strip() if follower_text else "0"
        except:
            profile_data['followers'] = "Bilinmiyor"
        print(f"👥 Takipçi: {profile_data['followers']}")
        
        # Takip edilen
        try:
            following_text = await page.eval_on_selector(
                'strong[data-e2e="following-count"], strong[title*="Takip"]',
                'el => el.textContent'
            )
            profile_data['following'] = following_text.strip() if following_text else "0"
        except:
            profile_data['following'] = "Bilinmiyor"
        print(f"👥 Takip edilen: {profile_data['following']}")
        
        # Biyografi
        try:
            bio = await page.eval_on_selector(
                'h2[data-e2e="user-bio"], div[class*="bio"]',
                'el => el.textContent'
            )
            profile_data['bio'] = bio.strip() if bio else "Biyografi yok"
        except:
            profile_data['bio'] = "Biyografi yok"
        print(f"📝 Biyografi: {profile_data['bio'][:50]}...")
        
        # ----- VİDEO LİNKLERİ -----
        video_links = []
        try:
            await page.wait_for_selector('div[data-e2e="user-post-item"]', timeout=30000)
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(3000)
            links = await page.eval_on_selector_all(
                'div[data-e2e="user-post-item"] a[href*="/video/"]',
                'els => els.map(el => el.href)'
            )
            video_links = list(set(links))[:10]
            print(f"🎥 Video linkleri: {len(video_links)}")
        except Exception as e:
            print(f"⚠️ Video linkleri alınamadı: {e}")
        
        # ----- REPOST LİNKLERİ -----
        repost_links = []
        try:
            repost_tab = await page.query_selector('div[data-e2e="repost-tab"]')
            if repost_tab:
                print("🔄 Repost sekmesi bulundu, tıklanıyor...")
                await repost_tab.click()
                await page.wait_for_timeout(10000)
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(2000)
                repost_links = await page.eval_on_selector_all(
                    'div[data-e2e="user-post-item"] a[href*="/video/"]',
                    'els => els.map(el => el.href)'
                )
                repost_links = list(set(repost_links))[:10]
                print(f"🔄 Repost linkleri: {len(repost_links)}")
            else:
                print("⚠️ Repost sekmesi yok.")
        except Exception as e:
            print(f"⚠️ Repost alınamadı: {e}")
        
        await browser.close()
        return profile_data, video_links, repost_links

def search_yandex_by_image(image_url, username):
    """
    Verilen görsel URL'sini Yandex'de arar, Instagram linklerini döndürür.
    """
    print(f"🔍 Yandex'te görsel arama yapılıyor...")
    found_links = []
    temp_filename = f"temp_{username}.jpg"
    
    try:
        # Görseli indir
        img_response = requests.get(image_url, timeout=15)
        img = Image.open(BytesIO(img_response.content))
        img.save(temp_filename)
        
        # Yandex'e yükle
        search_url = "https://yandex.com/images/search"
        files = {"upfile": (temp_filename, open(temp_filename, "rb"), "image/jpeg")}
        params = {"rpt": "imageview", "format": "json"}
        
        response = requests.post(search_url, params=params, files=files, timeout=30)
        
        # JSON cevabını parse et (Yandex'in yapısı karmaşık, sayfa kaynağına da bakalım)
        # Basit yöntem: Gelen sayfadaki tüm linkleri topla, instagram olanları filtrele
        soup = BeautifulSoup(response.text, 'html.parser')
        all_links = soup.find_all('a', href=True)
        
        instagram_pattern = re.compile(r'(https?://)?(www\.)?instagram\.com/[a-zA-Z0-9_.]+/?')
        for a in all_links:
            href = a['href']
            if instagram_pattern.search(href):
                found_links.append(href)
        
        # Bazen yönlendirme linkleri olabilir, temizle
        found_links = list(set(found_links))[:5]
        print(f"📸 Yandex'te {len(found_links)} Instagram linki bulundu.")
        
    except Exception as e:
        print(f"❌ Yandex arama hatası: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    
    return found_links

def check_username_similarity(tiktok_username, instagram_username):
    """
    İki kullanıcı adı arasındaki benzerlik oranını hesaplar (0-100).
    """
    if not instagram_username:
        return 0
    return fuzz.ratio(tiktok_username.lower(), instagram_username.lower())

def send_profile_to_discord(profile_data, username):
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
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
    except Exception as e:
        print(f"❌ Profil gönderme hatası: {e}")

def send_videos_to_discord(video_links, username, video_type="video"):
    if not video_links:
        return
    title = "🎥 Kendi Videoları" if video_type == "video" else "🔄 Repost Videoları"
    color = 0x00ff00 if video_type == "video" else 0xffaa00
    for link in video_links:
        embed = {
            "title": title,
            "url": link,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"@{username} • {video_type}"}
        }
        try:
            requests.post(webhook_url, json={"embeds": [embed]})
            time.sleep(1)
        except Exception as e:
            print(f"❌ Gönderme hatası: {e}")

def send_social_media_log(platform, profile_url, similarity_score, tiktok_username, avatar_url=None):
    """
    Bulunan sosyal medya profillerini Discord'a log olarak gönderir.
    """
    embed = {
        "title": f"🔍 {platform} Profili Bulundu",
        "url": profile_url,
        "color": 0xff69b4,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_username} ile bağlantılı olabilir"}
    }
    if avatar_url:
        embed["thumbnail"] = {"url": avatar_url}
    if similarity_score > 0:
        embed["fields"] = [
            {"name": "Kullanıcı Adı Benzerliği", "value": f"%{similarity_score}", "inline": True}
        ]
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
    except Exception as e:
        print(f"❌ Sosyal medya log gönderme hatası: {e}")

# ========== ANA FONKSİYON ==========
async def main():
    username = tiktok_user
    
    # Daha önce gönderilenleri takip için dosyalar (opsiyonel)
    sent_videos_file = "sent_videos.txt"
    sent_reposts_file = "sent_reposts.txt"
    sent_social_file = "sent_social.txt"
    
    try:
        with open(sent_videos_file, "r") as f:
            sent_videos = set(f.read().splitlines())
    except:
        sent_videos = set()
    
    try:
        with open(sent_reposts_file, "r") as f:
            sent_reposts = set(f.read().splitlines())
    except:
        sent_reposts = set()
    
    try:
        with open(sent_social_file, "r") as f:
            sent_social = set(f.read().splitlines())
    except:
        sent_social = set()
    
    profile_sent_file = "profile_sent.txt"
    try:
        with open(profile_sent_file, "r") as f:
            profile_sent = f.read().strip() == username
    except:
        profile_sent = False
    
    # TikTok verilerini al
    profile_data, video_links, repost_links = await get_tiktok_data(username)
    
    if not profile_data:
        print("❌ Profil verileri alınamadı.")
        return
    
    # Profil gönderimi (ilk defa)
    if not profile_sent:
        send_profile_to_discord(profile_data, username)
        with open(profile_sent_file, "w") as f:
            f.write(username)
        await asyncio.sleep(2)
        
        # Profil fotoğrafı varsa Yandex araması yap
        if profile_data.get('avatar'):
            instagram_links = search_yandex_by_image(profile_data['avatar'], username)
            for link in instagram_links:
                if link not in sent_social:
                    # Instagram kullanıcı adını çıkar
                    match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', link)
                    ig_username = match.group(1) if match else ""
                    similarity = check_username_similarity(username, ig_username)
                    send_social_media_log("Instagram", link, similarity, username, profile_data['avatar'])
                    sent_social.add(link)
                    time.sleep(1)
            # Gönderilen sosyal linkleri kaydet
            with open(sent_social_file, "w") as f:
                f.write("\n".join(sent_social))
    else:
        print("⏩ Profil daha önce gönderilmiş.")
    
    # Videoları gönder
    new_videos = [v for v in video_links if v not in sent_videos]
    if new_videos:
        send_videos_to_discord(new_videos, username, "video")
        for v in new_videos:
            sent_videos.add(v)
        with open(sent_videos_file, "w") as f:
            f.write("\n".join(sent_videos))
    
    # Repostları gönder
    new_reposts = [r for r in repost_links if r not in sent_reposts]
    if new_reposts:
        send_videos_to_discord(new_reposts, username, "repost")
        for r in new_reposts:
            sent_reposts.add(r)
        with open(sent_reposts_file, "w") as f:
            f.write("\n".join(sent_reposts))
    
    print("✅ Bot çalışması tamamlandı.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
