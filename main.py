print("🚀 BOT BAŞLADI!")

import os
import asyncio
import requests
import re
import time
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

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

async def get_tiktok_profile(username):
    """Sadece profil bilgilerini al (avatar, isim, takipçi, biyografi)"""
    print(f"🔍 TikTok profil bilgileri alınıyor: @{username}")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        profile_url = f"https://www.tiktok.com/@{username}"
        try:
            await page.goto(profile_url, timeout=60000)
            await page.wait_for_timeout(15000)
        except Exception as e:
            print(f"❌ Sayfa yüklenemedi: {e}")
            await browser.close()
            return None
        
        # Profil fotoğrafı
        avatar = None
        avatar_selectors = [
            'img[src*="avt"]',
            'img[alt*="avatar"]',
            'img[class*="avatar"]',
            'img[data-e2e="user-avatar"]'
        ]
        for sel in avatar_selectors:
            try:
                avatar = await page.eval_on_selector(sel, 'el => el.src')
                if avatar:
                    print(f"🖼 Avatar bulundu (seçici: {sel})")
                    break
            except:
                continue
        
        # İsim
        display_name = username
        try:
            name_elem = await page.query_selector('h1[data-e2e="user-title"]')
            if name_elem:
                display_name = await name_elem.text_content()
                display_name = display_name.strip()
        except:
            pass
        
        # Takipçi
        followers = "Bilinmiyor"
        try:
            follower_elem = await page.query_selector('strong[data-e2e="followers-count"]')
            if follower_elem:
                followers = await follower_elem.text_content()
                followers = followers.strip()
        except:
            pass
        
        # Takip edilen
        following = "Bilinmiyor"
        try:
            following_elem = await page.query_selector('strong[data-e2e="following-count"]')
            if following_elem:
                following = await following_elem.text_content()
                following = following.strip()
        except:
            pass
        
        # Biyografi
        bio = "Biyografi yok"
        try:
            bio_elem = await page.query_selector('h2[data-e2e="user-bio"]')
            if bio_elem:
                bio = await bio_elem.text_content()
                bio = bio.strip()
        except:
            pass
        
        await browser.close()
        
        return {
            'avatar': avatar,
            'display_name': display_name,
            'followers': followers,
            'following': following,
            'bio': bio
        }

def check_social_media_username(username):
    """
    Verilen kullanıcı adını Instagram, Twitter, Facebook, YouTube, Twitch'te dener.
    Sayfa var mı yok mu kontrol eder.
    Dönen: {platform: link, var_mı: bool}
    """
    platforms = {
        "Instagram": f"https://www.instagram.com/{username}/",
        "Twitter": f"https://twitter.com/{username}",
        "Facebook": f"https://www.facebook.com/{username}",
        "YouTube": f"https://www.youtube.com/@{username}",
        "Twitch": f"https://www.twitch.tv/{username}",
        "TikTok": f"https://www.tiktok.com/@{username}",  # zaten biliyoruz ama yine de
    }
    
    results = []
    for platform, url in platforms.items():
        try:
            response = requests.get(url, timeout=5, allow_redirects=True)
            # 200 OK dönerse sayfa var (bazı platformlar 404 dönmez, içerik kontrolü gerekebilir)
            if response.status_code == 200:
                # Basit bir içerik kontrolü: "Page not found" gibi ifadeler varsa geç
                if "not found" in response.text.lower() or "this page doesn't exist" in response.text.lower():
                    continue
                results.append((platform, url))
                print(f"✅ {platform} profili bulundu: {url}")
            else:
                print(f"❌ {platform} profili yok (HTTP {response.status_code})")
        except Exception as e:
            print(f"⚠️ {platform} kontrol edilirken hata: {e}")
    return results

def search_yandex_by_image(image_url, username):
    """
    Yandex Görsel'de ara, çıkan linklerden sosyal medya profillerini topla.
    """
    print(f"🔍 Yandex'te görsel arama yapılıyor...")
    found_profiles = []  # (platform, link) şeklinde
    
    temp_filename = f"temp_{username}.jpg"
    try:
        # Görseli indir
        img_response = requests.get(image_url, timeout=15)
        with open(temp_filename, "wb") as f:
            f.write(img_response.content)
        
        # Yandex'e yükle
        search_url = "https://yandex.com/images/search"
        files = {"upfile": (temp_filename, open(temp_filename, "rb"), "image/jpeg")}
        params = {"rpt": "imageview", "format": "json"}
        
        response = requests.post(search_url, params=params, files=files, timeout=30)
        
        # Sayfa kaynağını parse et
        soup = BeautifulSoup(response.text, 'html.parser')
        all_links = soup.find_all('a', href=True)
        
        # Sosyal medya platformlarını tanımla
        social_patterns = {
            "Instagram": r'(https?://)?(www\.)?instagram\.com/[a-zA-Z0-9_.]+/?',
            "Twitter": r'(https?://)?(www\.)?twitter\.com/[a-zA-Z0-9_]+/?',
            "Facebook": r'(https?://)?(www\.)?facebook\.com/[a-zA-Z0-9.]+/?',
            "YouTube": r'(https?://)?(www\.)?youtube\.com/(c|user|@|channel)/[a-zA-Z0-9_]+/?',
            "Twitch": r'(https?://)?(www\.)?twitch\.tv/[a-zA-Z0-9_]+/?',
            "TikTok": r'(https?://)?(www\.)?tiktok\.com/@[a-zA-Z0-9_.]+/?',
        }
        
        for a in all_links:
            href = a['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.IGNORECASE):
                    # Linki temizle
                    full_url = href if href.startswith('http') else 'https://' + href
                    found_profiles.append((platform, full_url))
                    print(f"📸 Yandex'te {platform} profili bulundu: {full_url}")
                    break  # bir link bir platforma ait, diğerlerine bakma
        
        # Tekrarları temizle
        found_profiles = list(set(found_profiles))[:10]  # en fazla 10 tane
        
    except Exception as e:
        print(f"❌ Yandex arama hatası: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    
    return found_profiles

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
        print("✅ Profil bilgileri gönderildi.")
    except Exception as e:
        print(f"❌ Profil gönderme hatası: {e}")

def send_social_media_log(platform, profile_url, similarity_score, tiktok_username, avatar_url=None, source="Kullanıcı Adı Taraması"):
    """
    Bulunan sosyal medya profillerini Discord'a log olarak gönderir.
    source: "Kullanıcı Adı Taraması" veya "Görsel Arama (Yandex)"
    """
    embed = {
        "title": f"🔍 {platform} Profili Bulundu ({source})",
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
        print(f"✅ {platform} log gönderildi.")
    except Exception as e:
        print(f"❌ Sosyal medya log gönderme hatası: {e}")

# ========== ANA FONKSİYON ==========
async def main():
    username = tiktok_user
    
    # Daha önce gönderilen sosyal medya linklerini takip et (tekrar gönderme)
    sent_social_file = "sent_social.txt"
    try:
        with open(sent_social_file, "r") as f:
            sent_social = set(f.read().splitlines())
    except:
        sent_social = set()
    
    # Profil bilgilerini al
    profile_data = await get_tiktok_profile(username)
    if not profile_data:
        print("❌ Profil bilgileri alınamadı.")
        return
    
    # Profil bilgilerini gönder (ilk defa, ama her seferinde gönderebiliriz, önemli değil)
    send_profile_to_discord(profile_data, username)
    await asyncio.sleep(2)
    
    # ----- 1. KULLANICI ADI TARAMASI -----
    print("\n🔎 Kullanıcı adı taraması başlıyor...")
    social_results = check_social_media_username(username)
    
    for platform, url in social_results:
        if url not in sent_social:
            # Benzerlik skoru: TikTok kullanıcı adı ile platformdaki kullanıcı adı aynı olduğu için %100
            similarity = 100
            send_social_media_log(platform, url, similarity, username, profile_data.get('avatar'), source="Kullanıcı Adı Taraması")
            sent_social.add(url)
            time.sleep(1)
        else:
            print(f"⏩ {url} daha önce gönderilmiş.")
    
    # ----- 2. GÖRSEL ARAMA (YANDEX) -----
    if profile_data.get('avatar'):
        print("\n🔎 Görsel arama (Yandex) başlıyor...")
        yandex_results = search_yandex_by_image(profile_data['avatar'], username)
        
        for platform, url in yandex_results:
            if url not in sent_social:
                # Platformdan kullanıcı adını çıkar, benzerlik hesapla
                match = re.search(rf'{platform.lower()}\.com/([a-zA-Z0-9_.@]+)', url, re.IGNORECASE)
                if match:
                    social_username = match.group(1).strip('/')
                    similarity = fuzz.ratio(username.lower(), social_username.lower())
                else:
                    similarity = 0
                send_social_media_log(platform, url, similarity, username, profile_data.get('avatar'), source="Görsel Arama (Yandex)")
                sent_social.add(url)
                time.sleep(1)
            else:
                print(f"⏩ {url} daha önce gönderilmiş.")
    else:
        print("⚠️ Profil fotoğrafı olmadığı için görsel arama yapılamadı.")
    
    # Gönderilen sosyal linkleri kaydet
    with open(sent_social_file, "w") as f:
        f.write("\n".join(sent_social))
    
    print("\n✅ Bot çalışması tamamlandı.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
