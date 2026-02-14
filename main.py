print("🚀 FBI AJANI BOT BAŞLADI!")

import os
import asyncio
import requests
import re
import time
import random
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# ========== ORTAM DEĞİŞKENLERİ ==========
webhook_url = os.environ.get("DISCORD_WEBHOOK")
tiktok_user = os.environ.get("TIKTOK_USER")

if not webhook_url or not tiktok_user:
    print("❌ DISCORD_WEBHOOK veya TIKTOK_USER eksik!")
    exit(1)

# ========== TEST MESAJI ==========
test_embed = {
    "title": "🧪 TEST MESAJI",
    "description": "FBI ajanı bot aktif.",
    "color": 0x0000ff
}
try:
    r = requests.post(webhook_url, json={"embeds": [test_embed]})
    print(f"📨 TEST MESAJI GÖNDERİLDİ: {r.status_code}")
except Exception as e:
    print(f"❌ TEST MESAJI HATASI: {e}")

# ========== RASTGELE USER-AGENT ==========
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
]

def get_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

# ========== PLATFORM LİSTESİ ==========
PLATFORMS = [
    {"name": "Instagram", "url": "https://www.instagram.com/{}/", "check": True},
    {"name": "Twitter", "url": "https://twitter.com/{}", "check": True},
    {"name": "Facebook", "url": "https://www.facebook.com/{}", "check": True},
    {"name": "YouTube", "url": "https://www.youtube.com/@{}", "check": True},
    {"name": "TikTok", "url": "https://www.tiktok.com/@{}", "check": True},
    {"name": "Twitch", "url": "https://www.twitch.tv/{}", "check": True},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}", "check": True},
    {"name": "Pinterest", "url": "https://www.pinterest.com/{}/", "check": True},
    {"name": "Tumblr", "url": "https://{}.tumblr.com", "check": True},
    {"name": "GitHub", "url": "https://github.com/{}", "check": True},
    {"name": "LinkedIn", "url": "https://www.linkedin.com/in/{}", "check": True},
    {"name": "Snapchat", "url": "https://www.snapchat.com/add/{}", "check": True},
    {"name": "Telegram", "url": "https://t.me/{}", "check": True},
    {"name": "Discord", "url": "https://discord.com/users/{}", "check": False}, # Discord ID gerektirir
]

# ========== TIKTOK PROFİL BİLGİLERİNİ ÇEK ==========
async def get_tiktok_profile(username):
    print(f"🔍 TikTok profil bilgileri alınıyor: @{username}")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        profile_url = f"https://www.tiktok.com/@{username}"
        try:
            await page.goto(profile_url, timeout=60000)
            await page.wait_for_timeout(8000)
        except Exception as e:
            print(f"❌ Sayfa yüklenemedi: {e}")
            await browser.close()
            return None
        
        # Avatar
        avatar_selectors = [
            'img[src*="avt"]',
            'img[alt*="avatar"]',
            'img[class*="avatar"]',
            'img[data-e2e="user-avatar"]'
        ]
        avatar = None
        for sel in avatar_selectors:
            try:
                avatar = await page.eval_on_selector(sel, 'el => el.src')
                if avatar:
                    break
            except:
                continue
        
        # İsim
        try:
            display_name = await page.eval_on_selector(
                'h1[data-e2e="user-title"], h1[class*="share-title"]',
                'el => el.textContent'
            )
            display_name = display_name.strip() if display_name else username
        except:
            display_name = username
        
        # Takipçi
        try:
            followers = await page.eval_on_selector(
                'strong[data-e2e="followers-count"]',
                'el => el.textContent'
            )
            followers = followers.strip()
        except:
            followers = "?"
        
        # Biyografi
        try:
            bio = await page.eval_on_selector(
                'h2[data-e2e="user-bio"]',
                'el => el.textContent'
            )
            bio = bio.strip() if bio else ""
        except:
            bio = ""
        
        await browser.close()
        
        return {
            "avatar": avatar,
            "display_name": display_name,
            "followers": followers,
            "bio": bio,
            "username": username
        }

# ========== KULLANICI ADI ARAMA (HTTP) ==========
def check_username_on_platforms(username):
    print("🔎 Kullanıcı adı taraması başlıyor...")
    found = []
    for platform in PLATFORMS:
        if not platform["check"]:
            continue
        url = platform["url"].format(username)
        try:
            # Rastgele bekle (rate-limit'i aşmak için)
            time.sleep(random.uniform(2, 5))
            response = requests.get(url, headers=get_headers(), timeout=10, allow_redirects=True)
            if response.status_code == 200:
                print(f"✅ {platform['name']} profili bulundu: {url}")
                # Sayfa başlığını al (varsa)
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title').text if soup.find('title') else ""
                found.append({
                    "platform": platform['name'],
                    "url": url,
                    "title": title[:100],
                    "method": "username_match"
                })
            elif response.status_code == 429:
                print(f"⚠️ {platform['name']} rate-limit (429), atlanıyor.")
            else:
                print(f"❌ {platform['name']} profili yok (HTTP {response.status_code})")
        except Exception as e:
            print(f"⚠️ {platform['name']} kontrol edilemedi: {e}")
    return found

# ========== GOOGLE'DA KULLANICI ADI ARAMA ==========
def search_username_on_google(username):
    print("🔎 Google'da kullanıcı adı aranıyor...")
    found = []
    try:
        time.sleep(random.uniform(3, 6))
        search_url = f"https://www.google.com/search?q={username}"
        response = requests.get(search_url, headers=get_headers(), timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Google sonuç linklerini topla
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'http' in href and not 'google.com' in href:
                    # Temizle
                    match = re.search(r'https?://[^&"]+', href)
                    if match:
                        url = match.group()
                        # Sadece sosyal medya domainlerini al
                        if any(domain in url for domain in ['instagram', 'twitter', 'facebook', 'tiktok', 'youtube', 'twitch', 'reddit']):
                            found.append({
                                "platform": "Google Sonuç",
                                "url": url,
                                "method": "google_search"
                            })
        else:
            print(f"⚠️ Google arama başarısız: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Google arama hatası: {e}")
    return found

# ========== YANDEX GÖRSEL ARAMA (Playwright ile) ==========
async def search_yandex_by_image_playwright(image_url, tiktok_username):
    print("🔍 Yandex Görsel'de (Playwright) arama yapılıyor...")
    found = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        try:
            # Yandex Görsel ana sayfası
            await page.goto("https://yandex.com/images/", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Dosya yükleme input'u
            file_input = await page.query_selector('input[type="file"]')
            if not file_input:
                print("❌ Yandex'te dosya yükleme input'u bulunamadı.")
                return []
            
            # Resmi indir ve geçici dosyaya kaydet
            img_data = requests.get(image_url, timeout=10).content
            temp_file = f"temp_{tiktok_username}.jpg"
            with open(temp_file, "wb") as f:
                f.write(img_data)
            
            # Dosyayı yükle
            await file_input.set_input_files(temp_file)
            await page.wait_for_timeout(8000)  # Arama sonuçlarının yüklenmesini bekle
            
            # Sayfadaki tüm linkleri topla
            links = await page.eval_on_selector_all(
                'a[href]',
                'els => els.map(el => el.href)'
            )
            
            # Sosyal medya linklerini filtrele
            for link in links:
                if any(domain in link for domain in ['instagram', 'twitter', 'facebook', 'tiktok', 'youtube', 'twitch', 'reddit']):
                    found.append({
                        "platform": "Yandex Görsel",
                        "url": link,
                        "method": "image_search"
                    })
            
            # Benzersiz yap
            unique = []
            seen = set()
            for item in found:
                if item['url'] not in seen:
                    seen.add(item['url'])
                    unique.append(item)
            
            print(f"📸 Yandex'te {len(unique)} sosyal medya linki bulundu.")
            return unique[:15]  # İlk 15
            
        except Exception as e:
            print(f"❌ Yandex arama hatası: {e}")
            return []
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            await browser.close()

# ========== DISCORD'A MESAJ GÖNDERME ==========
def send_profile_to_discord(profile):
    embed = {
        "title": f"👤 {profile['display_name']} (@{profile['username']})",
        "url": f"https://www.tiktok.com/@{profile['username']}",
        "color": 0x9b59b6,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "TikTok Profil Bilgileri"}
    }
    if profile.get('avatar'):
        embed["thumbnail"] = {"url": profile['avatar']}
    embed["fields"] = [
        {"name": "👥 Takipçi", "value": profile['followers'], "inline": True},
        {"name": "📝 Biyografi", "value": profile['bio'][:100] if profile['bio'] else "Yok", "inline": False}
    ]
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
        print("✅ Profil bilgileri gönderildi.")
    except Exception as e:
        print(f"❌ Profil gönderme hatası: {e}")

def send_social_media_log(item, tiktok_username, avatar_url=None):
    """
    item: {"platform": "...", "url": "...", "title": "...", "method": "..."}
    """
    if item["method"] == "username_match":
        color = 0x00ff00
        title = f"🔍 {item['platform']} Profili Bulundu (Kullanıcı Adı)"
    elif item["method"] == "google_search":
        color = 0xffaa00
        title = f"🌐 Google'da Bulundu: {item['platform']}"
    else:
        color = 0xff69b4
        title = f"🖼️ Görsel Arama Sonucu: {item['platform']}"
    
    embed = {
        "title": title,
        "url": item['url'],
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_username} ile bağlantılı olabilir"}
    }
    if avatar_url:
        embed["thumbnail"] = {"url": avatar_url}
    if item.get('title'):
        embed["description"] = item['title'][:200]
    
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
        print(f"📤 {item['platform']} log gönderildi.")
    except Exception as e:
        print(f"❌ Log gönderme hatası: {e}")

# ========== ANA FONKSİYON ==========
async def main():
    username = tiktok_user
    
    # Daha önce gönderilenleri takip et (basit dosya)
    sent_file = "sent_urls.txt"
    try:
        with open(sent_file, "r") as f:
            sent = set(f.read().splitlines())
    except:
        sent = set()
    
    # TikTok profil bilgileri
    profile = await get_tiktok_profile(username)
    if not profile:
        print("❌ Profil bilgileri alınamadı.")
        return
    
    # Profil bilgilerini gönder
    send_profile_to_discord(profile)
    
    # 1. Kullanıcı adı taraması (platformlar)
    username_results = check_username_on_platforms(username)
    for res in username_results:
        if res['url'] not in sent:
            send_social_media_log(res, username, profile.get('avatar'))
            sent.add(res['url'])
            time.sleep(1)
    
    # 2. Google araması
    google_results = search_username_on_google(username)
    for res in google_results:
        if res['url'] not in sent:
            send_social_media_log(res, username, profile.get('avatar'))
            sent.add(res['url'])
            time.sleep(1)
    
    # 3. Görsel arama (Yandex Playwright)
    if profile.get('avatar'):
        image_results = await search_yandex_by_image_playwright(profile['avatar'], username)
        for res in image_results:
            if res['url'] not in sent:
                send_social_media_log(res, username, profile.get('avatar'))
                sent.add(res['url'])
                time.sleep(1)
    else:
        print("⚠️ Avatar yok, görsel arama atlanıyor.")
    
    # Gönderilenleri kaydet
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
