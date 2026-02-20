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
    "name_search": 0x00aaff,
    "default": 0x9b59b6
}

# ========== ICON MAP ==========
ICON_MAP = {
    "instagram": "📸", "twitter": "🐦", "facebook": "📘", "youtube": "🎥",
    "twitch": "🎮", "reddit": "👽", "github": "🐙", "pinterest": "📌",
    "tumblr": "📝", "snapchat": "👻", "telegram": "✈️", "linkedin": "💼",
    "tiktok": "🎵", "onlyfans": "🔞"
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
        avatar = None
        try:
            avatar = await page.eval_on_selector('img[src*="avt"]', 'el => el.src')
        except:
            pass
        try:
            display_name = await page.eval_on_selector('h1[data-e2e="user-title"]', 'el => el.textContent')
            display_name = display_name.strip()
        except:
            display_name = username
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

# ========== KULLANICI ADI VARYASYONLARI (akıllı) ==========
def generate_username_variations(username):
    # Temizle: sadece harf, rakam, nokta, tire, alt çizgi kalmalı (boşlukları at)
    import re
    base = re.sub(r'[^a-zA-Z0-9]', '', username)
    if not base:
        base = username
    variations = set()
    variations.add(base)
    variations.add(base.lower())
    variations.add(base.upper())
    variations.add(base.capitalize())
    if len(base) > 3:
        variations.add('.'.join(base))
        variations.add('-'.join(base))
        variations.add('_'.join(base))
    for i in range(1, 4):
        variations.add(f"{base}{i}")
        variations.add(f"{base}_{i}")
        variations.add(f"{base}-{i}")
    # Uzunluk kontrolü (3-30 arası, geçerli karakterler)
    valid_variations = []
    for v in variations:
        if 3 <= len(v) <= 30 and re.match(r'^[a-zA-Z0-9._-]+$', v):
            valid_variations.append(v)
    return valid_variations[:20]

# ========== İSİM VARYASYONLARI ==========
def generate_name_variations(display_name):
    if not display_name or display_name == tiktok_user:
        return []
    variations = set()
    variations.add(display_name)
    variations.add(display_name.lower())
    variations.add(display_name.upper())
    variations.add(display_name.title())
    variations.add(display_name.replace(' ', ''))
    variations.add(display_name.replace(' ', '.'))
    variations.add(display_name.replace(' ', '_'))
    if ' ' in display_name:
        parts = display_name.split()
        if len(parts) >= 2:
            variations.add(parts[0])
            variations.add(parts[-1])
            variations.add(f"{parts[0]} {parts[-1][0]}")
    return list(variations)[:15]

# ========== TAHMİNİ İSİM ÜRET ==========
def generate_name_from_username(username):
    parts = re.split(r'[._-]', username)
    cleaned = []
    for part in parts:
        letters = re.sub(r'\d+', '', part)
        if letters:
            cleaned.append(letters.capitalize())
    if not cleaned:
        cleaned = [username.capitalize()]
    if len(cleaned) >= 2:
        return f"{cleaned[0]} {cleaned[1]}"
    else:
        return cleaned[0]

# ========== AKILLI PLATFORM KONTROLÜ ==========
async def check_platform(session, platform, username):
    # Platformun kullanıcı adı kurallarına uygun mu?
    if platform["name"] == "Twitter" and len(username) > 15:
        return None
    if platform["name"] == "Instagram" and len(username) > 30:
        return None
    # Tumblr için geçersiz karakterler varsa atla
    if platform["name"] == "Tumblr" and not re.match(r'^[a-zA-Z0-9-]+$', username):
        return None
    
    url = platform["url"].format(username)
    try:
        async with session.get(url, timeout=15, allow_redirects=True, ssl=False) as response:
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
        # Hataları sessizce geç (çok fazla spam yapmasın)
        return None

# ========== USER-SEARCHER (2000+ PLATFORM) ==========
async def search_user_searcher(username):
    print(f"🔍 User-Searcher'da taranıyor: {username}")
    results = []
    try:
        url = f"https://user-searcher.com/search?q={username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if any(x in href for x in ['instagram.com', 'twitter.com', 'facebook.com', 'tiktok.com', 'youtube.com', 'reddit.com', 'github.com']):
                            results.append({
                                "url": href,
                                "platform": href.split('.')[1] if '.' in href else "unknown",
                                "source": "User-Searcher"
                            })
    except Exception as e:
        print(f"❌ User-Searcher hatası: {e}")
    return results[:20]

# ========== İSİM ARAMA FONKSİYONLARI ==========
async def search_pipl(name):
    print(f"🔍 Pipl'de isim aranıyor: {name}")
    results = []
    try:
        url = f"https://pipl.com/search/?q={quote_plus(name)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    summary = soup.find('div', class_='summary')
                    if summary:
                        results.append({
                            "source": "Pipl",
                            "summary": summary.text[:500],
                            "url": url
                        })
    except Exception as e:
        print(f"❌ Pipl hatası: {e}")
    return results

async def search_spokeo(name):
    print(f"🔍 Spokeo'da isim aranıyor: {name}")
    results = []
    try:
        url = f"https://www.spokeo.com/{quote_plus(name)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    preview = soup.find('div', class_='preview')
                    if preview:
                        results.append({
                            "source": "Spokeo",
                            "preview": preview.text[:500],
                            "url": url
                        })
    except Exception as e:
        print(f"❌ Spokeo hatası: {e}")
    return results

async def search_zabasearch(name):
    print(f"🔍 ZabaSearch'de isim aranıyor: {name}")
    results = []
    try:
        url = f"http://www.zabasearch.com/people/{quote_plus(name)}/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    for result in soup.find_all('div', class_='result'):
                        results.append({
                            "source": "ZabaSearch",
                            "text": result.text[:300],
                            "url": url
                        })
    except Exception as e:
        print(f"❌ ZabaSearch hatası: {e}")
    return results[:10]

async def search_thatsthem(name):
    print(f"🔍 Thatsthem'de isim aranıyor: {name}")
    results = []
    try:
        url = f"https://thatsthem.com/name/{quote_plus(name)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    for person in soup.find_all('div', class_='person'):
                        name_elem = person.find('div', class_='name')
                        if name_elem:
                            results.append({
                                "source": "Thatsthem",
                                "name": name_elem.text,
                                "details": person.text[:300],
                                "url": url
                            })
    except Exception as e:
        print(f"❌ Thatsthem hatası: {e}")
    return results[:5]

# ========== GÖRSEL ARAMA (Yandex + Google + Bing) ==========
async def search_yandex(image_url, tiktok_username):
    results = []
    temp_filename = f"temp_{tiktok_username}.jpg"
    try:
        img_response = requests.get(image_url, timeout=15)
        img = Image.open(BytesIO(img_response.content))
        img.save(temp_filename)
        search_url = "https://yandex.com/images/search"
        files = {"upfile": (temp_filename, open(temp_filename, "rb"), "image/jpeg")}
        params = {"rpt": "imageview", "format": "json"}
        response = requests.post(search_url, params=params, files=files, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(x in href for x in ['instagram.com', 'twitter.com', 'facebook.com', 'tiktok.com']):
                full_url = href if href.startswith('http') else 'https://' + href
                results.append({"url": full_url, "source": "Yandex", "title": a.text[:100] if a.text else ""})
    except Exception as e:
        print(f"❌ Yandex hatası: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    return results

async def search_google(image_url, tiktok_username):
    results = []
    try:
        search_url = f"https://www.google.com/searchbyimage?image_url={quote_plus(image_url)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'http' in href and any(x in href for x in ['instagram.com', 'twitter.com']):
                results.append({"url": href, "source": "Google", "title": a.text[:100] if a.text else ""})
    except Exception as e:
        print(f"❌ Google hatası: {e}")
    return results

async def search_bing(image_url, tiktok_username):
    results = []
    try:
        search_url = f"https://www.bing.com/images/searchbyimage?cbir=1&imgurl={quote_plus(image_url)}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'instagram.com' in href or 'twitter.com' in href:
                results.append({"url": href, "source": "Bing", "title": a.text[:100] if a.text else ""})
    except Exception as e:
        print(f"❌ Bing hatası: {e}")
    return results

# ========== SIZINTI ARAMA ==========
async def search_dehashed(query, query_type="email"):
    print(f"🔍 DeHashed'de {query_type} aranıyor: {query}")
    try:
        url = f"https://dehashed.com/search?query={quote_plus(query)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    result_count = soup.find('div', class_='result-count')
                    if result_count:
                        count_text = result_count.text
                        numbers = re.findall(r'\d+', count_text)
                        if numbers:
                            return {"found": int(numbers[0]), "url": url, "preview": count_text}
    except Exception as e:
        print(f"❌ DeHashed hatası: {e}")
    return {"found": 0}

async def search_leak_lookup(email):
    if not LEAK_LOOKUP_API_KEY:
        return None
    try:
        url = "https://leak-lookup.com/api/search"
        params = {"key": LEAK_LOOKUP_API_KEY, "type": "email_address", "query": email}
        response = requests.post(url, data=params, timeout=15)
        data = response.json()
        if data.get('error') == 'false':
            return {"found": True, "count": len(data.get('result', {})), "sources": list(data.get('result', {}).keys())}
    except Exception as e:
        print(f"❌ Leak-Lookup hatası: {e}")
    return {"found": False}

# ========== DISCORD'A MESAJ GÖNDERME ==========
def send_to_discord(embed_data):
    try:
        response = requests.post(webhook_url, json={"embeds": [embed_data]})
        return response.status_code in [200, 204]
    except:
        return False

def send_tiktok_profile(profile):
    embed = {
        "title": f"🎵 TikTok Profili: @{profile['username']}",
        "url": f"https://www.tiktok.com/@{profile['username']}",
        "color": COLORS["tiktok"],
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "Fedai Bot Ultimate • Profil Bilgileri"}
    }
    if profile.get('avatar'):
        embed["thumbnail"] = {"url": profile['avatar']}
    fields = [
        {"name": "👤 İsim", "value": profile['display_name'], "inline": True},
        {"name": "👥 Takipçi", "value": str(profile['followers']), "inline": True},
        {"name": "👥 Takip", "value": str(profile['following']), "inline": True},
    ]
    if profile.get('emails'):
        fields.append({"name": "📧 Biyografide Email", "value": ", ".join(profile['emails']), "inline": False})
    if profile.get('phones'):
        fields.append({"name": "📞 Biyografide Telefon", "value": ", ".join(profile['phones']), "inline": False})
    if profile.get('urls'):
        fields.append({"name": "🔗 Biyografide Linkler", "value": "\n".join(profile['urls'][:3]), "inline": False})
    if profile.get('bio'):
        fields.append({"name": "📝 Biyografi", "value": profile['bio'][:200], "inline": False})
    embed["fields"] = fields
    send_to_discord(embed)
    time.sleep(1)

def send_platform_group(platform_name, profiles, tiktok_avatar, tiktok_user):
    # Sadece benzerliği 100 olanları filtrele
    profiles = [p for p in profiles if p.get('similarity', 0) >= 100]
    if not profiles:
        return
    color = COLORS.get(platform_name.lower(), COLORS["default"])
    icon = ICON_MAP.get(platform_name.lower(), "🔗")
    
    profiles.sort(key=lambda x: x['similarity'], reverse=True)
    fields = []
    for p in profiles[:5]:
        guessed_name = generate_name_from_username(p['username'])
        name = f"@{p['username']} (benzerlik %{p['similarity']})"
        value = f"👤 Tahmini: {guessed_name} (kesin değil)\n[Profili görüntüle]({p['url']})"
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

def send_name_search_results(results, tiktok_user, tiktok_avatar):
    if not results:
        return
    embed = {
        "title": f"👤 İsim Arama Sonuçları – {len(results)} kaynak",
        "color": COLORS["name_search"],
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • İsim bazlı tarama"},
        "fields": []
    }
    if tiktok_avatar:
        embed["thumbnail"] = {"url": tiktok_avatar}
    for res in results[:5]:
        embed["fields"].append({
            "name": res.get('source', 'Kaynak'),
            "value": res.get('summary', res.get('preview', res.get('text', 'Bilgi yok')))[:200],
            "inline": False
        })
    send_to_discord(embed)
    time.sleep(1)

def send_image_search_group(results, tiktok_avatar, tiktok_user, search_type="Görsel Arama"):
    if not results:
        return
    fields = []
    for res in results[:8]:
        name = f"🔍 {res['source']}"
        value = f"[{res['url'][:50]}...]({res['url']})"
        if res.get('title'):
            value += f"\n{res['title'][:100]}"
        fields.append({"name": name, "value": value, "inline": False})
    if len(results) > 8:
        fields.append({"name": "Diğerleri", "value": f"+{len(results)-8} sonuç daha", "inline": False})
    embed = {
        "title": f"🖼️ {search_type} – {len(results)} bağlantı",
        "color": 0xffaa00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Görsel benzerliği"},
        "fields": fields
    }
    if tiktok_avatar:
        embed["thumbnail"] = {"url": tiktok_avatar}
    send_to_discord(embed)
    time.sleep(1)

def send_leak_report(leak_data, query, tiktok_user):
    if not leak_data or leak_data.get('found', 0) == 0:
        return
    embed = {
        "title": f"💥 Sızıntı Tespit Edildi: {query}",
        "color": COLORS["leak"],
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Veri sızıntısı"},
        "fields": []
    }
    if leak_data.get('found'):
        embed["fields"].append({
            "name": "🔍 DeHashed",
            "value": f"{leak_data['found']} sonuç bulundu. Detaylar ücretli.",
            "inline": False
        })
    if leak_data.get('sources'):
        embed["fields"].append({
            "name": "📋 Leak-Lookup",
            "value": f"Kaynaklar: {', '.join(leak_data['sources'][:3])}",
            "inline": False
        })
    send_to_discord(embed)
    time.sleep(1)

def send_domain_report(domain_data, domain, tiktok_user):
    if not domain_data:
        return
    embed = {
        "title": f"🌐 Domain Bilgileri: {domain}",
        "color": COLORS["domain"],
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Domain taraması"},
        "fields": []
    }
    if domain_data.get('hostname'):
        embed["fields"].append({
            "name": "SecurityTrails",
            "value": f"Hostname: {domain_data['hostname']}\nAlexa Rank: {domain_data.get('alexa_rank', 'N/A')}",
            "inline": False
        })
    send_to_discord(embed)
    time.sleep(1)

def send_archive_report(archive_data, url, tiktok_user):
    embed = {
        "title": f"📦 Arşiv Bilgileri",
        "color": COLORS["archive"],
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Arşiv taraması"},
        "fields": []
    }
    if archive_data.get('available'):
        embed["fields"].append({
            "name": "Wayback Machine",
            "value": f"[Arşivlenmiş]({archive_data['url']}) - {archive_data['timestamp']}",
            "inline": False
        })
    else:
        embed["fields"].append({
            "name": "Wayback Machine",
            "value": "Arşiv bulunamadı",
            "inline": False
        })
    send_to_discord(embed)
    time.sleep(1)

def send_summary_report(stats, tiktok_user):
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
    
    profile = await get_tiktok_profile(username)
    if not profile:
        print("❌ TikTok profili alınamadı.")
        return
    
    send_tiktok_profile(profile)
    
    stats = defaultdict(int)
    found_by_platform = defaultdict(list)
    
    # Kullanıcı adı varyasyonları
    variations = generate_username_variations(username)
    print(f"📝 {len(variations)} kullanıcı adı varyasyonu test edilecek.")
    
    # Platform listesi
    PLATFORMS = [
        {"name": "Instagram", "url": "https://www.instagram.com/{}"},
        {"name": "Twitter", "url": "https://twitter.com/{}"},
        {"name": "Facebook", "url": "https://www.facebook.com/{}"},
        {"name": "YouTube", "url": "https://www.youtube.com/@{}"},
        {"name": "Twitch", "url": "https://www.twitch.tv/{}"},
        {"name": "Reddit", "url": "https://www.reddit.com/user/{}"},
        {"name": "GitHub", "url": "https://github.com/{}"},
        {"name": "Pinterest", "url": "https://www.pinterest.com/{}"},
        {"name": "Tumblr", "url": "https://{}.tumblr.com"},
        {"name": "Snapchat", "url": "https://www.snapchat.com/add/{}"},
        {"name": "Telegram", "url": "https://t.me/{}"},
        {"name": "LinkedIn", "url": "https://www.linkedin.com/in/{}"},
        {"name": "TikTok (farklı hesap)", "url": "https://www.tiktok.com/@{}"},
    ]
    
    async with aiohttp.ClientSession() as session:
        for var_username in variations:
            print(f"\n🔎 Test ediliyor: '{var_username}'")
            for platform in PLATFORMS:
                result = await check_platform(session, platform, var_username)
                if result:
                    identifier = f"{platform['name']}:{result['url']}"
                    if identifier not in sent:
                        similarity = fuzz.ratio(username.lower(), var_username.lower())
                        # Sadece %100 benzerlik olanları ekle
                        if similarity >= 100:
                            found_by_platform[platform['name']].append({
                                "username": var_username,
                                "url": result['url'],
                                "similarity": similarity,
                                "followers": result.get('followers'),
                                "avatar": result.get('avatar')
                            })
                            sent.add(identifier)
                            stats[f"{platform['name']} profili"] += 1
                    await asyncio.sleep(1.5)
            await asyncio.sleep(1)
    
    # User-Searcher
    user_searcher_results = await search_user_searcher(username)
    for res in user_searcher_results:
        identifier = f"us:{res['url']}"
        if identifier not in sent:
            # User-Searcher sonuçları için benzerlik 100 kabul ediyoruz
            found_by_platform[res['platform']].append({
                "username": username,
                "url": res['url'],
                "similarity": 100,
                "source": res['source']
            })
            sent.add(identifier)
            stats["User-Searcher profili"] += 1
    
    # Gruplanmış platform raporları
    for platform_name, profiles in found_by_platform.items():
        send_platform_group(platform_name, profiles, profile.get('avatar'), username)
    
    # İsim taraması (display_name farklıysa)
    if profile['display_name'] and profile['display_name'] != username:
        name_variations = generate_name_variations(profile['display_name'])
        print(f"📝 {len(name_variations)} isim varyasyonu test edilecek.")
        all_name_results = []
        for name in name_variations[:3]:
            all_name_results.extend(await search_pipl(name))
            all_name_results.extend(await search_spokeo(name))
            all_name_results.extend(await search_zabasearch(name))
            all_name_results.extend(await search_thatsthem(name))
        if all_name_results:
            send_name_search_results(all_name_results, username, profile.get('avatar'))
            stats["İsim arama"] += len(all_name_results)
    
    # Görsel arama
    if profile.get('avatar'):
        print("\n🔎 Görsel arama başlıyor...")
        yandex = await search_yandex(profile['avatar'], username)
        google = await search_google(profile['avatar'], username)
        bing = await search_bing(profile['avatar'], username)
        all_image = yandex + google + bing
        if all_image:
            send_image_search_group(all_image, profile.get('avatar'), username, "Çoklu Görsel Arama")
            stats["Görsel arama"] += len(all_image)
    
    # Sızıntı taraması
    if profile.get('emails'):
        for email in profile['emails']:
            dehashed = await search_dehashed(email, "email")
            if dehashed.get('found', 0) > 0:
                send_leak_report(dehashed, email, username)
                stats["Sızıntı"] += 1
            leak = await search_leak_lookup(email)
            if leak and leak.get('found'):
                send_leak_report(leak, email, username)
                stats["Sızıntı"] += 1
    
    # Domain taraması
    if profile.get('urls'):
        for url in profile['urls']:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain:
                # Wayback Machine
                wayback = await check_wayback_machine(url)
                if wayback.get('available'):
                    send_archive_report(wayback, url, username)
                    stats["Arşiv"] += 1
    
    # Özet rapor
    send_summary_report(stats, username)
    
    with open(sent_file, "w") as f:
        f.write("\n".join(sent))
    
    print(f"\n✅ Bot çalışması tamamlandı. Toplam {sum(stats.values())} yeni bulgu.")

# Wayback Machine fonksiyonu (eklenmemişti)
async def check_wayback_machine(url):
    try:
        api_url = f"https://archive.org/wayback/available?url={quote_plus(url)}"
        response = requests.get(api_url, timeout=10)
        data = response.json()
        if data.get('archived_snapshots', {}).get('closest', {}).get('available'):
            snapshot = data['archived_snapshots']['closest']
            return {"available": True, "url": snapshot.get('url'), "timestamp": snapshot.get('timestamp')}
    except:
        pass
    return {"available": False}

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
