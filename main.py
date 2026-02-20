print("🚀 FEDAI BOT ULTIMATE BAŞLADI!")

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
from collections import defaultdict

# ========== ORTAM DEĞİŞKENLERİ ==========
webhook_url = os.environ.get("DISCORD_WEBHOOK")
tiktok_user = os.environ.get("TIKTOK_USER")

if not webhook_url or not tiktok_user:
    print("❌ DISCORD_WEBHOOK veya TIKTOK_USER eksik!")
    exit(1)

# ========== API ANAHTARLARI (ücretsiz) ==========
SKYBIOMETRY_CLIENT_ID = os.environ.get("SKYBIOMETRY_CLIENT_ID")
SKYBIOMETRY_CLIENT_SECRET = os.environ.get("SKYBIOMETRY_CLIENT_SECRET")
LEAK_LOOKUP_API_KEY = os.environ.get("LEAK_LOOKUP_API_KEY")
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY")
SECURITY_TRAILS_API_KEY = os.environ.get("SECURITY_TRAILS_API_KEY")

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
    "leak": 0xFF0000,
    "email": 0x00FF00,
    "domain": 0x0000FF,
    "archive": 0x800080,
    "default": 0x9b59b6
}

# ========== TEST MESAJI ==========
test_embed = {
    "title": "🧪 FEDAI BOT ULTIMATE AKTİF",
    "description": f"TikTok kullanıcısı: @{tiktok_user}\nDetaylı ultra tarama başlıyor...",
    "color": 0x00ff00
}
try:
    r = requests.post(webhook_url, json={"embeds": [test_embed]})
    print(f"📨 TEST MESAJI GÖNDERİLDİ: {r.status_code}")
except Exception as e:
    print(f"❌ TEST MESAJI HATASI: {e}")

# ========== KULLANICI ADI GEÇERLİLİK KONTROLÜ ==========
def is_valid_username_for_platform(username, platform_name):
    """Platforma göre kullanıcı adı geçerlilik kontrolü"""
    import re
    if not username or len(username) < 1:
        return False
    if platform_name == "Twitter":
        # Twitter: 4-15 karakter, harf, rakam, alt çizgi
        return 4 <= len(username) <= 15 and re.match(r'^[a-zA-Z0-9_]+$', username)
    elif platform_name == "Tumblr":
        # Tumblr: 3-32 karakter, harf, rakam, tire (domain olarak kullanılır)
        return 3 <= len(username) <= 32 and re.match(r'^[a-zA-Z0-9-]+$', username)
    elif platform_name == "Instagram":
        # Instagram: 1-30 karakter, harf, rakam, nokta, alt çizgi
        return 1 <= len(username) <= 30 and re.match(r'^[a-zA-Z0-9._]+$', username)
    # Diğer platformlar için genel kontrol
    return 1 <= len(username) <= 50 and re.match(r'^[a-zA-Z0-9._-]+$', username)

# ========== KULLANICI ADI VARYASYONLARI ==========
def generate_username_variations(username):
    """Farklı kullanıcı adı varyasyonları üret, en mantıklıları önce gelecek şekilde sırala"""
    # Temizle: sadece harf, rakam, nokta, tire, alt çizgi kalmalı
    base = re.sub(r'[^a-zA-Z0-9]', '', username)  # özel karakterleri temizle
    if not base:
        base = username
    
    variations = []
    variations.append((base, 100))
    variations.append((base.lower(), 99))
    variations.append((base.upper(), 80))
    variations.append((base.capitalize(), 95))
    
    if len(base) > 3:
        variations.append(('.'.join(base), 85))
    variations.append(('-'.join(base), 84))
    variations.append(('_'.join(base), 83))
    
    for i in range(1, 4):
        variations.append((f"{base}{i}", 90 - i))
        variations.append((f"{base}_{i}", 89 - i))
        variations.append((f"{base}-{i}", 88 - i))
    
    if len(base) > 5:
        variations.append((base[:int(len(base)/2)], 70))
    
    # Benzersiz yap ve önceliğe göre sırala
    unique = {}
    for u, p in variations:
        if u not in unique or p > unique[u]:
            unique[u] = p
    
    sorted_vars = sorted(unique.items(), key=lambda x: x[1], reverse=True)
    return [v[0] for v in sorted_vars[:20]]

# ========== İSİM VARYASYONLARI ==========
def generate_name_variations(display_name):
    """Display name'den isim-soyisim varyasyonları üret"""
    if not display_name:
        return []
    
    variations = [display_name]
    variations.append(display_name.lower())
    variations.append(display_name.upper())
    variations.append(display_name.title())
    variations.append(display_name.replace(' ', ''))
    variations.append(display_name.replace(' ', '.'))
    variations.append(display_name.replace(' ', '_'))
    
    if ' ' in display_name:
        parts = display_name.split()
        if len(parts) >= 2:
            variations.append(parts[0])
            variations.append(parts[-1])
            variations.append(f"{parts[0]} {parts[-1][0]}")
    
    return list(set(variations))[:10]

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
        except Exception as e:
            print(f"❌ TikTok sayfası yüklenemedi: {e}")
            await browser.close()
            return None
        
        avatar = None
        try:
            avatar = await page.eval_on_selector('img[src*="avt"]', 'el => el.src')
        except:
            pass
        
        display_name = username
        try:
            display_name = await page.eval_on_selector('h1[data-e2e="user-title"]', 'el => el.textContent')
            display_name = display_name.strip()
        except:
            pass
        
        followers = following = "?"
        try:
            followers = await page.eval_on_selector('strong[data-e2e="followers-count"]', 'el => el.textContent')
        except:
            pass
        try:
            following = await page.eval_on_selector('strong[data-e2e="following-count"]', 'el => el.textContent')
        except:
            pass
        
        bio = ""
        try:
            bio = await page.eval_on_selector('h2[data-e2e="user-bio"]', 'el => el.textContent')
        except:
            pass
        
        await browser.close()
        
        # Biyografiden email, telefon, website, sosyal medya linklerini çıkar
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', bio)
        phones = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', bio)
        urls = re.findall(r'https?://[^\s]+', bio)
        
        return {
            "avatar": avatar,
            "display_name": display_name,
            "followers": followers,
            "following": following,
            "bio": bio,
            "username": username,
            "emails": emails,
            "phones": phones,
            "urls": urls
        }

# ========== AKILLI PLATFORM KONTROLÜ ==========
async def check_platform(session, platform, username):
    """Bir platformda kullanıcı adını kontrol et, gerçekten var mı yok mu doğrula"""
    # Önce kullanıcı adının platform için geçerli olup olmadığını kontrol et
    if not is_valid_username_for_platform(username, platform["name"]):
        return None
    
    url = platform["url"].format(username)
    # Twitter için özel header (header boyutu sorununu aşmak için)
    headers = {'User-Agent': 'Mozilla/5.0'} if platform["name"] == "Twitter" else None
    
    try:
        async with session.get(url, timeout=15, allow_redirects=True, ssl=False, headers=headers) as response:
            if response.status != 200:
                return None
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            page_title = soup.find('title').text if soup.find('title') else ""
            
            # Genel "not found" anahtar kelimeleri
            not_found_keywords = [
                "not found", "page not found", "sayfa bulunamadı", "bu hesap mevcut değil",
                "this account doesn't exist", "sorry, this page isn't available",
                "hesap askıya alındı", "bu içerik şu anda mevcut değil", "there's nothing here",
                "sorry, we couldn't find that page", "sorry, nobody on reddit goes by that name"
            ]
            for keyword in not_found_keywords:
                if keyword.lower() in html.lower() or keyword.lower() in page_title.lower():
                    return None
            
            # Platforma özel kontroller
            if platform["name"] == "Instagram":
                if 'x1e56ztr' not in html and 'profilePage' not in html:
                    return None
                h1 = soup.find('h1')
                if h1 and ('üzgünüz' in h1.text.lower() or 'sorry' in h1.text.lower()):
                    return None
            
            elif platform["name"] == "Twitter":
                if 'data-testid="UserName"' not in html and 'data-testid="UserAvatar"' not in html:
                    return None
            
            elif platform["name"] == "YouTube":
                if 'kanal mevcut değil' in html.lower() or 'this channel doesn\'t exist' in html.lower():
                    return None
            
            elif platform["name"] == "Twitch":
                if "sorry. unless you’ve got a time machine" in html.lower():
                    return None
            
            elif platform["name"] == "Reddit":
                if "böyle bir kullanıcı yok" in html.lower() or "nobody on reddit goes by that name" in html.lower():
                    return None
            
            # Profil bilgilerini topla
            profile_info = {
                "url": str(response.url),
                "title": page_title[:150],
                "description": "",
                "avatar": None,
                "followers": None
            }
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                profile_info["description"] = meta_desc.get('content', '')[:200]
            
            og_image = soup.find('meta', property='og:image')
            if og_image:
                profile_info["avatar"] = og_image.get('content', '')
            
            # Takipçi sayısı (platforma özel)
            if platform["name"] == "Instagram":
                followers_match = re.search(r'"edge_followed_by":{"count":(\d+)}', html)
                if followers_match:
                    profile_info["followers"] = followers_match.group(1)
            elif platform["name"] == "Twitter":
                followers_match = re.search(r'"followers_count":(\d+)', html)
                if followers_match:
                    profile_info["followers"] = followers_match.group(1)
            
            return profile_info
            
    except Exception as e:
        print(f"⚠️ {platform['name']} hatası: {e}")
        return None

# ========== USER-SEARCHER (2000+ PLATFORM) ==========
async def search_user_searcher(username):
    """User-Searcher'da kullanıcı adı ara (2000+ platform)"""
    print(f"🔍 User-Searcher'da taranıyor: {username}")
    results = []
    try:
        url = f"https://user-searcher.com/search?q={username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if any(x in href for x in ['instagram.com', 'twitter.com', 'facebook.com', 'tiktok.com', 'youtube.com', 'reddit.com', 'github.com', 'pinterest.com', 'tumblr.com']):
                            results.append({
                                "url": href,
                                "platform": href.split('.')[1] if '.' in href else "unknown",
                                "source": "User-Searcher"
                            })
    except Exception as e:
        print(f"❌ User-Searcher hatası: {e}")
    
    return results[:20]

# ========== İSİM ARAMA (GOOGLE) ==========
async def search_name_on_platforms(name, tiktok_avatar, tiktok_user):
    """İsim varyasyonlarını Google'da ara ve sosyal medya linklerini bul"""
    print(f"🔍 İsim aranıyor: {name}")
    name_variations = generate_name_variations(name)
    results = []
    async with aiohttp.ClientSession() as session:
        for var_name in name_variations[:5]:  # İlk 5 varyasyon
            search_url = f"https://www.google.com/search?q={quote_plus(var_name)}"
            try:
                async with session.get(search_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if any(x in href for x in ['instagram.com', 'twitter.com', 'facebook.com', 'tiktok.com']):
                                results.append({
                                    "url": href,
                                    "source": "Google",
                                    "name": var_name
                                })
            except:
                pass
            await asyncio.sleep(1)
    
    if results:
        embed = {
            "title": f"👤 İsim Arama Sonuçları: {name}",
            "color": 0x00aaff,
            "fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"@{tiktok_user} • İsim bazlı tarama"}
        }
        if tiktok_avatar:
            embed["thumbnail"] = {"url": tiktok_avatar}
        
        for res in results[:5]:
            embed["fields"].append({
                "name": res['source'],
                "value": f"[{res['url']}]({res['url']})"
            })
        
        send_to_discord(embed)
        return len(results)
    return 0

# ========== DISCORD'A MESAJ GÖNDERME ==========
def send_to_discord(embed_data):
    """Genel Discord gönderme fonksiyonu"""
    try:
        response = requests.post(webhook_url, json={"embeds": [embed_data]})
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"❌ Discord gönderme hatası: {e}")
        return False

def send_platform_group(platform_name, profiles, tiktok_avatar, tiktok_user):
    if not profiles:
        return
    color = COLORS.get(platform_name.lower(), COLORS["default"])
    icon = next((p["icon"] for p in PLATFORMS if p["name"] == platform_name), "🔗")
    
    fields = []
    for p in profiles[:5]:
        name = f"@{p['username']} (benzerlik %{p['similarity']})"
        value = f"[Profili görüntüle]({p['url']})"
        if p.get('followers'):
            value += f"\n👥 {p['followers']} takipçi"
        fields.append({"name": name, "value": value, "inline": False})
    
    if len(profiles) > 5:
        fields.append({"name": "Diğerleri", "value": f"+{len(profiles)-5} profil daha", "inline": False})
    
    embed = {
        "title": f"{icon} {platform_name} – {len(profiles)} profil bulundu",
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} ile bağlantılı • Gruplandırılmış rapor"},
        "fields": fields
    }
    if tiktok_avatar:
        embed["thumbnail"] = {"url": tiktok_avatar}
    
    send_to_discord(embed)
    time.sleep(1)

def send_summary_report(stats, tiktok_user):
    """Tarama özeti"""
    total = sum(stats.values())
    description = f"Toplam **{total}** bulgu.\n"
    for key, count in stats.items():
        description += f"\n{key}: {count}"
    
    embed = {
        "title": "📊 Tarama Raporu",
        "description": description,
        "color": 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Ultra tarama tamamlandı"}
    }
    send_to_discord(embed)

# ========== ANA FONKSİYON ==========
async def main():
    username = tiktok_user
    print(f"🔍 Hedef kullanıcı: @{username}")
    
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
    
    # TikTok profilini gönder (her zaman)
    embed_profile = {
        "title": f"🎵 TikTok Profili: @{profile['username']}",
        "url": f"https://www.tiktok.com/@{profile['username']}",
        "color": COLORS["tiktok"],
        "thumbnail": {"url": profile['avatar']} if profile['avatar'] else None,
        "fields": [
            {"name": "👤 İsim", "value": profile['display_name'], "inline": True},
            {"name": "👥 Takipçi", "value": str(profile['followers']), "inline": True},
            {"name": "👥 Takip", "value": str(profile['following']), "inline": True},
            {"name": "📝 Biyografi", "value": profile['bio'][:200] if profile['bio'] else "Yok", "inline": False}
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Fedai Bot Pro • Profil Bilgileri"}
    }
    if embed_profile["thumbnail"] is None:
        del embed_profile["thumbnail"]
    send_to_discord(embed_profile)
    time.sleep(2)
    
    stats = defaultdict(int)
    found_by_platform = defaultdict(list)
    
    # 2. Kullanıcı adı varyasyonları oluştur
    variations = generate_username_variations(username)
    print(f"📝 {len(variations)} kullanıcı adı varyasyonu test edilecek.")
    
    # 3. Platform taraması (ana)
    PLATFORMS = [
        {"name": "Instagram", "url": "https://www.instagram.com/{}", "icon": "📸"},
        {"name": "Twitter", "url": "https://twitter.com/{}", "icon": "🐦"},
        {"name": "Facebook", "url": "https://www.facebook.com/{}", "icon": "📘"},
        {"name": "YouTube", "url": "https://www.youtube.com/@{}", "icon": "🎥"},
        {"name": "Twitch", "url": "https://www.twitch.tv/{}", "icon": "🎮"},
        {"name": "Reddit", "url": "https://www.reddit.com/user/{}", "icon": "👽"},
        {"name": "GitHub", "url": "https://github.com/{}", "icon": "🐙"},
        {"name": "Pinterest", "url": "https://www.pinterest.com/{}", "icon": "📌"},
        {"name": "Tumblr", "url": "https://{}.tumblr.com", "icon": "📝"},
        {"name": "Snapchat", "url": "https://www.snapchat.com/add/{}", "icon": "👻"},
        {"name": "Telegram", "url": "https://t.me/{}", "icon": "✈️"},
        {"name": "LinkedIn", "url": "https://www.linkedin.com/in/{}", "icon": "💼"},
        {"name": "TikTok (farklı hesap)", "url": "https://www.tiktok.com/@{}", "icon": "🎵"},
    ]
    
    async with aiohttp.ClientSession() as session:
        for var_username in variations:
            print(f"\n🔎 Test ediliyor: '{var_username}'")
            for platform in PLATFORMS:
                # Tumblr için özel: domain oluştururken geçerli karakterler
                if platform["name"] == "Tumblr" and not re.match(r'^[a-zA-Z0-9-]+$', var_username):
                    continue
                
                result = await check_platform(session, platform, var_username)
                if result:
                    identifier = f"{platform['name']}:{result['url']}"
                    if identifier not in sent:
                        similarity = fuzz.ratio(username.lower(), var_username.lower())
                        # SADECE %100 BENZERLİK
                        if similarity == 100:
                            found_by_platform[platform['name']].append({
                                "username": var_username,
                                "url": result['url'],
                                "similarity": similarity,
                                "followers": result.get('followers'),
                                "avatar": result.get('avatar')
                            })
                            sent.add(identifier)
                            stats[f"{platform['name']} profili"] += 1
                            print(f"✅ {platform['name']}: {var_username} (benzerlik %{similarity})")
                    await asyncio.sleep(1.5)
            await asyncio.sleep(1)
    
    # 4. User-Searcher taraması
    user_searcher_results = await search_user_searcher(username)
    for res in user_searcher_results:
        identifier = f"us:{res['url']}"
        if identifier not in sent:
            found_by_platform[res['platform']].append({
                "username": username,
                "url": res['url'],
                "similarity": 100,
                "source": res['source']
            })
            sent.add(identifier)
            stats["User-Searcher profili"] += 1
    
    # 5. Gruplanmış platform raporları
    for platform_name, profiles in found_by_platform.items():
        if profiles:
            send_platform_group(platform_name, profiles, profile.get('avatar'), username)
    
    # 6. İsim araması (display_name varsa ve username'den farklıysa)
    if profile['display_name'] and profile['display_name'] != username:
        name_count = await search_name_on_platforms(profile['display_name'], profile.get('avatar'), username)
        if name_count:
            stats["İsim arama"] += name_count
    
    # 7. Özet rapor
    send_summary_report(stats, username)
    
    # Gönderilenleri kaydet
    with open(sent_file, "w") as f:
        f.write("\n".join(sent))
    
    print(f"\n✅ Bot çalışması tamamlandı. Toplam {sum(stats.values())} yeni bulgu.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
