print("🚀 FEDAI BOT BAŞLADI!")

import os
import asyncio
import requests
import re
import time
import json
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from fuzzywuzzy import fuzz
import aiohttp
from urllib.parse import urlparse, quote_plus

# ========== ORTAM DEĞİŞKENLERİ ==========
webhook_url = os.environ.get("DISCORD_WEBHOOK")
tiktok_user = os.environ.get("TIKTOK_USER")

if not webhook_url or not tiktok_user:
    print("❌ DISCORD_WEBHOOK veya TIKTOK_USER eksik!")
    exit(1)

# ========== RENKLER ==========
COLORS = {
    "tiktok": 0x010101,
    "instagram": 0xE1306C,
    "twitter": 0x1DA1F2,
    "facebook": 0x4267B2,
    "youtube": 0xFF0000,
    "twitch": 0x9146FF,
    "reddit": 0xFF4500,
    "github": 0x333333,
    "pinterest": 0xE60023,
    "tumblr": 0x35465C,
    "snapchat": 0xFFFC00,
    "discord": 0x5865F2,
    "telegram": 0x26A5E4,
    "linkedin": 0x0077B5,
    "onlyfans": 0x00AFF0,
    "default": 0x9b59b6
}

# ========== PLATFORM LİSTESİ ==========
PLATFORMS = [
    {"name": "Instagram", "url": "https://www.instagram.com/{}", "icon": "📸", "check_profile": True},
    {"name": "Twitter", "url": "https://twitter.com/{}", "icon": "🐦", "check_profile": True},
    {"name": "Facebook", "url": "https://www.facebook.com/{}", "icon": "📘", "check_profile": True},
    {"name": "YouTube", "url": "https://www.youtube.com/@{}", "icon": "🎥", "check_profile": True},
    {"name": "Twitch", "url": "https://www.twitch.tv/{}", "icon": "🎮", "check_profile": True},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}", "icon": "👽", "check_profile": True},
    {"name": "GitHub", "url": "https://github.com/{}", "icon": "🐙", "check_profile": True},
    {"name": "Pinterest", "url": "https://www.pinterest.com/{}", "icon": "📌", "check_profile": True},
    {"name": "Tumblr", "url": "https://{}.tumblr.com", "icon": "📝", "check_profile": True},
    {"name": "Snapchat", "url": "https://www.snapchat.com/add/{}", "icon": "👻", "check_profile": False},
    {"name": "Discord", "url": "https://discord.com/users/{}", "icon": "💬", "check_profile": False},
    {"name": "Telegram", "url": "https://t.me/{}", "icon": "✈️", "check_profile": True},
    {"name": "LinkedIn", "url": "https://www.linkedin.com/in/{}", "icon": "💼", "check_profile": True},
    {"name": "OnlyFans", "url": "https://onlyfans.com/{}", "icon": "🔞", "check_profile": False},
    {"name": "TikTok (farklı hesap)", "url": "https://www.tiktok.com/@{}", "icon": "🎵", "check_profile": True},
]

# ========== TEST MESAJI ==========
test_embed = {
    "title": "🧪 FEDAI BOT AKTİF",
    "description": f"TikTok kullanıcısı: @{tiktok_user}\nDetaylı tarama başlıyor...",
    "color": 0x00ff00
}
try:
    r = requests.post(webhook_url, json={"embeds": [test_embed]})
    print(f"📨 TEST MESAJI GÖNDERİLDİ: {r.status_code}")
except Exception as e:
    print(f"❌ TEST MESAJI HATASI: {e}")

# ========== KULLANICI ADI VARYASYONLARI ==========
def generate_username_variations(username):
    """Farklı kullanıcı adı varyasyonları üret"""
    variations = [username]
    
    # Nokta ekleme
    if len(username) > 3:
        variations.append(username.replace('', '.')[1:-1])  # a.r.a.s.i
    
    # Tire ekleme
    variations.append(username.replace('', '-')[1:-1])
    
    # Alt çizgi ekleme
    variations.append(username.replace('', '_')[1:-1])
    
    # Sayı ekleme
    for i in range(1, 4):
        variations.append(f"{username}{i}")
        variations.append(f"{username}_{i}")
    
    # Kısaltmalar
    variations.append(username[:int(len(username)/2)])
    
    # Büyük-küçük harf
    variations.append(username.lower())
    variations.append(username.upper())
    variations.append(username.capitalize())
    
    return list(set(variations))[:15]  # Max 15 varyasyon

# ========== TIKTOK PROFİL BİLGİLERİ ==========
async def get_tiktok_profile(username):
    print(f"🔍 TikTok profil bilgileri alınıyor: @{username}")
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        profile_url = f"https://www.tiktok.com/@{username}"
        try:
            await page.goto(profile_url, timeout=60000)
            await page.wait_for_timeout(8000)
        except:
            await browser.close()
            return None
        
        # Avatar
        avatar_selectors = ['img[src*="avt"]', 'img[alt*="avatar"]', 'img[class*="avatar"]']
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
            display_name = await page.eval_on_selector('h1[data-e2e="user-title"]', 'el => el.textContent')
        except:
            display_name = username
        
        # Takipçi/Takip
        followers, following = "?", "?"
        try:
            followers = await page.eval_on_selector('strong[data-e2e="followers-count"]', 'el => el.textContent')
        except:
            pass
        try:
            following = await page.eval_on_selector('strong[data-e2e="following-count"]', 'el => el.textContent')
        except:
            pass
        
        # Biyografi
        bio = ""
        try:
            bio = await page.eval_on_selector('h2[data-e2e="user-bio"]', 'el => el.textContent')
        except:
            pass
        
        await browser.close()
        
        return {
            "avatar": avatar,
            "display_name": display_name.strip() if display_name else username,
            "followers": followers,
            "following": following,
            "bio": bio,
            "username": username
        }

# ========== PLATFORM KONTROLÜ ==========
async def check_platform(session, platform, username):
    """Bir platformda kullanıcı adını kontrol et, detaylı bilgi topla"""
    url = platform["url"].format(username)
    try:
        async with session.get(url, timeout=10, allow_redirects=True, ssl=False) as response:
            if response.status == 200:
                # Sayfa içeriğini al
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Profil bilgilerini topla
                profile_info = {
                    "url": str(response.url),
                    "status": response.status,
                    "title": soup.find('title').text if soup.find('title') else "",
                    "description": "",
                    "followers": None,
                    "avatar": None
                }
                
                # Meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    profile_info["description"] = meta_desc.get('content', '')
                
                # Open graph image (avatar olabilir)
                og_image = soup.find('meta', property='og:image')
                if og_image:
                    profile_info["avatar"] = og_image.get('content', '')
                
                return profile_info
            else:
                return {"status": response.status, "url": url}
    except Exception as e:
        return {"status": "error", "url": url, "error": str(e)}

# ========== GÖRSEL ARAMA (ÇOKLU MOTOR) ==========
async def search_image_multi_engine(image_url, tiktok_username):
    """Yandex, Google, Bing, TinEye'da görsel ara"""
    print(f"🔍 Çoklu görsel arama başlıyor...")
    all_results = []
    
    # Yandex
    yandex_results = await search_yandex(image_url, tiktok_username)
    all_results.extend(yandex_results)
    
    # Google (basit scraping)
    google_results = await search_google(image_url, tiktok_username)
    all_results.extend(google_results)
    
    # Bing
    bing_results = await search_bing(image_url, tiktok_username)
    all_results.extend(bing_results)
    
    # TinEye (ücretli API gerektirir, şimdilik pasif)
    # tineye_results = await search_tineye(image_url, tiktok_username)
    # all_results.extend(tineye_results)
    
    # Benzersiz yap
    unique_results = []
    seen = set()
    for r in all_results:
        if r['url'] not in seen:
            seen.add(r['url'])
            unique_results.append(r)
    
    return unique_results[:15]  # Max 15 sonuç

async def search_yandex(image_url, tiktok_username):
    """Yandex görsel arama"""
    results = []
    temp_filename = f"temp_{tiktok_username}.jpg"
    
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
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Linkleri topla
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(x in href for x in ['instagram.com', 'twitter.com', 'facebook.com', 'tiktok.com']):
                full_url = href if href.startswith('http') else 'https://' + href
                results.append({
                    "url": full_url,
                    "source": "Yandex",
                    "title": a.text[:100] if a.text else ""
                })
    except Exception as e:
        print(f"❌ Yandex hatası: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    
    return results

async def search_google(image_url, tiktok_username):
    """Google Görsel arama (basit)"""
    results = []
    try:
        search_url = f"https://www.google.com/searchbyimage?image_url={quote_plus(image_url)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Benzer görseller linklerini bul
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'http' in href and any(x in href for x in ['instagram.com', 'twitter.com']):
                results.append({
                    "url": href,
                    "source": "Google",
                    "title": a.text[:100] if a.text else ""
                })
    except Exception as e:
        print(f"❌ Google hatası: {e}")
    
    return results

async def search_bing(image_url, tiktok_username):
    """Bing Görsel arama"""
    results = []
    try:
        search_url = f"https://www.bing.com/images/searchbyimage?cbir=1&imgurl={quote_plus(image_url)}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'instagram.com' in href or 'twitter.com' in href:
                results.append({
                    "url": href,
                    "source": "Bing",
                    "title": a.text[:100] if a.text else ""
                })
    except Exception as e:
        print(f"❌ Bing hatası: {e}")
    
    return results

# ========== PROFİL ANALİZİ ==========
async def analyze_profile(url, platform_name):
    """Bir profilin içindeki linkleri ve bağlantıları analiz et"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10, ssl=False) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Tüm linkleri topla
                    links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http') and not href.startswith(url):
                            links.append(href)
                    
                    # Sosyal medya linklerini filtrele
                    social_links = []
                    social_pattern = re.compile(r'(instagram\.com|twitter\.com|facebook\.com|tiktok\.com|youtube\.com)')
                    for link in links[:20]:  # İlk 20 link
                        if social_pattern.search(link):
                            social_links.append(link)
                    
                    return social_links
    except:
        return []
    return []

# ========== DISCORD'A MESAJ GÖNDERME ==========
def send_to_discord(embed_data):
    """Genel Discord gönderme fonksiyonu"""
    try:
        response = requests.post(webhook_url, json={"embeds": [embed_data]})
        return response.status_code in [200, 204]
    except:
        return False

def send_profile_embed(profile):
    """TikTok profil bilgilerini gönder"""
    embed = {
        "title": f"🎵 TikTok Profili: @{profile['username']}",
        "url": f"https://www.tiktok.com/@{profile['username']}",
        "color": COLORS["tiktok"],
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Fedai Bot • Profil Bilgileri"}
    }
    if profile.get('avatar'):
        embed["thumbnail"] = {"url": profile['avatar']}
    
    fields = []
    fields.append({"name": "👤 İsim", "value": profile['display_name'], "inline": True})
    fields.append({"name": "👥 Takipçi", "value": str(profile['followers']), "inline": True})
    fields.append({"name": "👥 Takip", "value": str(profile['following']), "inline": True})
    
    if profile.get('bio'):
        fields.append({"name": "📝 Biyografi", "value": profile['bio'][:200], "inline": False})
    
    embed["fields"] = fields
    send_to_discord(embed)
    time.sleep(1)

def send_platform_embed(platform_name, url, profile_info, tiktok_user, avatar_url=None, similarity=None):
    """Bulunan platform profilini gönder"""
    color = COLORS.get(platform_name.lower(), COLORS["default"])
    icon = next((p["icon"] for p in PLATFORMS if p["name"] == platform_name), "🔗")
    
    embed = {
        "title": f"{icon} {platform_name} Profili Bulundu",
        "url": url,
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} ile bağlantılı • Kaynak: Username Match"}
    }
    
    if avatar_url:
        embed["thumbnail"] = {"url": avatar_url}
    
    fields = []
    if profile_info.get('title'):
        fields.append({"name": "📌 Başlık", "value": profile_info['title'][:100], "inline": False})
    if profile_info.get('description'):
        fields.append({"name": "📝 Açıklama", "value": profile_info['description'][:200], "inline": False})
    if similarity:
        fields.append({"name": "🎯 Benzerlik", "value": f"%{similarity}", "inline": True})
    
    if fields:
        embed["fields"] = fields
    
    send_to_discord(embed)
    time.sleep(1)

def send_image_search_embed(result, tiktok_user, avatar_url=None):
    """Görsel arama sonuçlarını gönder"""
    embed = {
        "title": f"🖼️ Görsel Arama Sonucu ({result['source']})",
        "url": result['url'],
        "color": 0xffaa00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Görsel benzerliği"}
    }
    if avatar_url:
        embed["thumbnail"] = {"url": avatar_url}
    if result.get('title'):
        embed["description"] = result['title'][:200]
    
    send_to_discord(embed)
    time.sleep(1)

def send_summary_report(found_counts, tiktok_user):
    """Tarama özet raporu gönder"""
    total = sum(found_counts.values())
    summary = f"Toplam {total} profil bulundu.\n"
    for platform, count in found_counts.items():
        summary += f"{platform}: {count} "
    
    embed = {
        "title": "📊 Tarama Raporu",
        "description": summary,
        "color": 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Tarama tamamlandı"}
    }
    send_to_discord(embed)

# ========== ANA FONKSİYON ==========
async def main():
    username = tiktok_user
    print(f"🔍 Hedef kullanıcı: @{username}")
    
    # Daha önce gönderilenleri takip et
    sent_file = "sent_profiles.txt"
    try:
        with open(sent_file, "r") as f:
            sent = set(f.read().splitlines())
    except:
        sent = set()
    
    # 1. TikTok profil bilgilerini al
    profile = await get_tiktok_profile(username)
    if not profile:
        print("❌ TikTok profili alınamadı.")
        return
    
    send_profile_embed(profile)
    
    found_counts = {}
    all_found_profiles = []
    
    # 2. Kullanıcı adı varyasyonları oluştur
    variations = generate_username_variations(username)
    print(f"📝 {len(variations)} kullanıcı adı varyasyonu test edilecek.")
    
    # 3. Tüm varyasyonları tüm platformlarda dene
    async with aiohttp.ClientSession() as session:
        for var_username in variations:
            print(f"\n🔎 Test ediliyor: '{var_username}'")
            
            for platform in PLATFORMS:
                # Kullanıcı adı formatını platforma göre ayarla
                test_username = var_username
                if platform["name"] == "Tumblr":
                    # Tumblr'da username.domain şeklinde
                    test_username = var_username
                
                result = await check_platform(session, platform, test_username)
                
                if isinstance(result, dict) and result.get("status") == 200:
                    # Profil bulundu
                    identifier = f"{platform['name']}:{result['url']}"
                    
                    if identifier not in sent:
                        # Benzerlik hesapla
                        similarity = fuzz.ratio(username.lower(), test_username.lower())
                        
                        send_platform_embed(
                            platform_name=platform['name'],
                            url=result['url'],
                            profile_info=result,
                            tiktok_user=username,
                            avatar_url=profile.get('avatar'),
                            similarity=similarity
                        )
                        
                        sent.add(identifier)
                        all_found_profiles.append(result['url'])
                        
                        # Platform sayacı
                        found_counts[platform['name']] = found_counts.get(platform['name'], 0) + 1
                        
                        # Profil içindeki linkleri analiz et
                        if platform.get('check_profile', False):
                            social_links = await analyze_profile(result['url'], platform['name'])
                            for link in social_links[:3]:
                                link_id = f"link:{link}"
                                if link_id not in sent:
                                    embed = {
                                        "title": f"🔗 {platform['name']} profilinden bulunan bağlantı",
                                        "url": link,
                                        "color": 0x00aaff,
                                        "footer": {"text": f"@{username} • Otomatik keşif"}
                                    }
                                    if profile.get('avatar'):
                                        embed["thumbnail"] = {"url": profile['avatar']}
                                    send_to_discord(embed)
                                    sent.add(link_id)
                                    time.sleep(1)
                    
                    # Rate limit koruması
                    await asyncio.sleep(2)
                else:
                    # Profil yoksa sessizce geç
                    pass
            
            await asyncio.sleep(1)  # Varyasyonlar arası bekle
    
    # 4. Görsel arama (profil fotoğrafı varsa)
    if profile.get('avatar'):
        print("\n🔎 Görsel arama başlıyor...")
        image_results = await search_image_multi_engine(profile['avatar'], username)
        
        for res in image_results[:10]:  # İlk 10 sonuç
            identifier = f"image:{res['url']}"
            if identifier not in sent:
                send_image_search_embed(res, username, profile.get('avatar'))
                sent.add(identifier)
                await asyncio.sleep(2)
    
    # 5. Özet rapor
    if found_counts:
        send_summary_report(found_counts, username)
    
    # Gönderilenleri kaydet
    with open(sent_file, "w") as f:
        f.write("\n".join(sent))
    
    print(f"\n✅ Bot çalışması tamamlandı. {len(all_found_profiles)} yeni profil bulundu.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
