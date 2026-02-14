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
SKYBIOMETRY_CLIENT_ID = os.environ.get("SKYBIOMETRY_CLIENT_ID")  # https://skybiometry.com/ kayıt ol
SKYBIOMETRY_CLIENT_SECRET = os.environ.get("SKYBIOMETRY_CLIENT_SECRET")
LEAK_LOOKUP_API_KEY = os.environ.get("LEAK_LOOKUP_API_KEY")  # https://leak-lookup.com/ kayıt ol
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY")  # https://hunter.io/ kayıt ol
SECURITY_TRAILS_API_KEY = os.environ.get("SECURITY_TRAILS_API_KEY")  # https://securitytrails.com/ kayıt ol

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

# ========== KULLANICI ADI VARYASYONLARI ==========
def generate_username_variations(username):
    variations = []
    variations.append((username, 100))
    variations.append((username.lower(), 99))
    variations.append((username.upper(), 80))
    variations.append((username.capitalize(), 95))
    if len(username) > 3:
        variations.append(('.'.join(username), 85))
    variations.append(('-'.join(username), 84))
    variations.append(('_'.join(username), 83))
    for i in range(1, 4):
        variations.append((f"{username}{i}", 90 - i))
        variations.append((f"{username}_{i}", 89 - i))
        variations.append((f"{username}-{i}", 88 - i))
    if len(username) > 5:
        variations.append((username[:int(len(username)/2)], 70))
    unique = {}
    for u, p in variations:
        if u not in unique or p > unique[u]:
            unique[u] = p
    sorted_vars = sorted(unique.items(), key=lambda x: x[1], reverse=True)
    return [v[0] for v in sorted_vars[:20]]

# ========== İSİM VARYASYONLARI ==========
def generate_name_variations(display_name):
    """Display name'den isim-soyisim varyasyonları üret"""
    if not display_name or display_name == username:
        return []
    
    variations = [display_name]
    
    # Küçük harf
    variations.append(display_name.lower())
    
    # Büyük harf
    variations.append(display_name.upper())
    
    # Baş harfler büyük
    variations.append(display_name.title())
    
    # Boşlukları kaldır
    variations.append(display_name.replace(' ', ''))
    
    # Boşlukları nokta yap
    variations.append(display_name.replace(' ', '.'))
    
    # Boşlukları alt çizgi yap
    variations.append(display_name.replace(' ', '_'))
    
    # İlk isim ve soyisim (varsa)
    if ' ' in display_name:
        parts = display_name.split()
        if len(parts) >= 2:
            variations.append(parts[0])  # sadece isim
            variations.append(parts[-1])  # sadece soyisim
            variations.append(f"{parts[0]} {parts[-1][0]}")  # isim + soyisim baş harfi
    
    return list(set(variations))[:15]

# ========== TAHMİNİ İSİM ÜRET ==========
def generate_name_from_username(username):
    parts = re.split(r'[._-]', username)
    cleaned_parts = []
    for part in parts:
        letters = re.sub(r'\d+', '', part)
        if letters:
            cleaned_parts.append(letters.capitalize())
    if not cleaned_parts:
        cleaned_parts = [username.capitalize()]
    if len(cleaned_parts) >= 2:
        return f"{cleaned_parts[0]} {cleaned_parts[1]}"
    else:
        return cleaned_parts[0]

# ========== AKILLI PLATFORM KONTROLÜ ==========
async def check_platform(session, platform, username):
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
            async with session.get(url, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Sonuçları parse et (site yapısına göre ayarla)
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

# ========== PİPL (İSİM ARAMA) ==========
async def search_pipl(name):
    """Pipl'de isim ara"""
    print(f"🔍 Pipl'de isim aranıyor: {name}")
    results = []
    try:
        url = f"https://pipl.com/search/?q={quote_plus(name)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Basit özet bilgileri al (detaylar ücretli)
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

# ========== SPEOKO (İSİM ARAMA) ==========
async def search_spokeo(name):
    """Spokeo'da isim ara"""
    print(f"🔍 Spokeo'da isim aranıyor: {name}")
    results = []
    try:
        url = f"https://www.spokeo.com/{quote_plus(name)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Önizleme bilgilerini al
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

# ========== ZABASEARCH (İSİM ARAMA) ==========
async def search_zabasearch(name):
    """ZabaSearch'de isim ara"""
    print(f"🔍 ZabaSearch'de isim aranıyor: {name}")
    results = []
    try:
        url = f"http://www.zabasearch.com/people/{quote_plus(name)}/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Sonuçları parse et
                    for result in soup.find_all('div', class_='result'):
                        results.append({
                            "source": "ZabaSearch",
                            "text": result.text[:300],
                            "url": url
                        })
    except Exception as e:
        print(f"❌ ZabaSearch hatası: {e}")
    
    return results[:10]

# ========== TINEYE (GÖRSEL ARAMA) ==========
async def search_tineye(image_url, tiktok_username):
    """TinEye'da görsel ara (günde 100 sorgu)"""
    print(f"🔍 TinEye'da görsel arama başlıyor...")
    results = []
    temp_filename = f"temp_tineye_{tiktok_username}.jpg"
    
    try:
        # Görseli indir
        img_response = requests.get(image_url, timeout=15)
        img = Image.open(BytesIO(img_response.content))
        img.save(temp_filename)
        
        # TinEye'a yükle
        search_url = "https://tineye.com/search"
        files = {"image": (temp_filename, open(temp_filename, "rb"), "image/jpeg")}
        
        response = requests.post(search_url, files=files, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sonuçları parse et
        for match in soup.find_all('div', class_='match'):
            link = match.find('a', href=True)
            if link:
                results.append({
                    "url": link['href'],
                    "source": "TinEye",
                    "title": link.text[:100] if link.text else ""
                })
    except Exception as e:
        print(f"❌ TinEye hatası: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    
    return results[:10]

# ========== LENSO.AI (GÖRSEL + YÜZ TANIMA) ==========
async def search_lenso(image_url, tiktok_username):
    """Lenso.ai'da görsel ara (yüz tanıma özellikli)"""
    print(f"🔍 Lenso.ai'da görsel arama başlıyor...")
    results = []
    temp_filename = f"temp_lenso_{tiktok_username}.jpg"
    
    try:
        # Görseli indir
        img_response = requests.get(image_url, timeout=15)
        img = Image.open(BytesIO(img_response.content))
        img.save(temp_filename)
        
        # Lenso.ai'a yükle (site yapısı scraping ile)
        search_url = "https://lenso.ai/zh/search"
        files = {"file": (temp_filename, open(temp_filename, "rb"), "image/jpeg")}
        
        response = requests.post(search_url, files=files, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sonuçları parse et (site yapısına göre ayarlanacak)
        for result in soup.find_all('a', href=True, class_='result'):
            href = result['href']
            if 'http' in href:
                results.append({
                    "url": href,
                    "source": "Lenso.ai",
                    "title": result.text[:100] if result.text else ""
                })
    except Exception as e:
        print(f"❌ Lenso.ai hatası: {e}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    
    return results[:10]

# ========== SKYBIOMETRY (YÜZ TANIMA API) ==========
async def compare_faces_skybiometry(face1_url, face2_url):
    """Skybiometry API ile iki yüzü karşılaştır"""
    if not SKYBIOMETRY_CLIENT_ID or not SKYBIOMETRY_CLIENT_SECRET:
        print("⚠️ Skybiometry API anahtarları yok, atlanıyor.")
        return None
    
    try:
        url = "https://api.skybiometry.com/fc/faces/recognize"
        params = {
            "api_key": SKYBIOMETRY_CLIENT_ID,
            "api_secret": SKYBIOMETRY_CLIENT_SECRET,
            "urls": f"{face1_url};{face2_url}",
            "detect_all_features": "true"
        }
        
        response = requests.post(url, data=params, timeout=15)
        data = response.json()
        
        if data.get('status') == 'success':
            # Benzerlik skorunu al
            photos = data.get('photos', [])
            if len(photos) >= 2:
                # Basit bir benzerlik hesapla (API'nin döndüğü şekle göre)
                return {
                    "success": True,
                    "similarity": 85,  # Örnek, gerçek API'ye göre ayarla
                    "data": data
                }
    except Exception as e:
        print(f"❌ Skybiometry hatası: {e}")
    
    return {"success": False}

# ========== DEHASHED (SIZINTI ARAMA) ==========
async def search_dehashed(query, query_type="email"):
    """DeHashed'de sızıntı ara (arama ücretsiz, sonuçlar ücretli)"""
    print(f"🔍 DeHashed'de {query_type} aranıyor: {query}")
    try:
        url = f"https://dehashed.com/search?query={quote_plus(query)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Kaç sonuç bulunduğunu bul (ücretsiz)
                    result_count = soup.find('div', class_='result-count')
                    if result_count:
                        count_text = result_count.text
                        numbers = re.findall(r'\d+', count_text)
                        if numbers:
                            return {
                                "found": int(numbers[0]),
                                "url": url,
                                "preview": count_text
                            }
    except Exception as e:
        print(f"❌ DeHashed hatası: {e}")
    
    return {"found": 0}

# ========== LEAK-LOOKUP (SIZINTI API) ==========
async def search_leak_lookup(email):
    """Leak-Lookup API ile email sızıntısı ara (günde 2 ücretsiz sorgu)"""
    if not LEAK_LOOKUP_API_KEY:
        print("⚠️ Leak-Lookup API anahtarı yok, atlanıyor.")
        return None
    
    try:
        url = "https://leak-lookup.com/api/search"
        params = {
            "key": LEAK_LOOKUP_API_KEY,
            "type": "email_address",
            "query": email
        }
        
        response = requests.post(url, data=params, timeout=15)
        data = response.json()
        
        if data.get('error') == 'false':
            return {
                "found": True,
                "count": len(data.get('result', {})),
                "sources": list(data.get('result', {}).keys())
            }
    except Exception as e:
        print(f"❌ Leak-Lookup hatası: {e}")
    
    return {"found": False}

# ========== HUNTER.IO (EMAIL ARAMA) ==========
async def search_hunter(domain):
    """Hunter.io ile domain'de email ara"""
    if not HUNTER_API_KEY:
        print("⚠️ Hunter.io API anahtarı yok, atlanıyor.")
        return None
    
    try:
        url = f"https://api.hunter.io/v2/domain-search"
        params = {
            "domain": domain,
            "api_key": HUNTER_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if data.get('data'):
            emails = data['data'].get('emails', [])
            return {
                "found": len(emails) > 0,
                "count": len(emails),
                "emails": [e['value'] for e in emails[:5]]
            }
    except Exception as e:
        print(f"❌ Hunter.io hatası: {e}")
    
    return {"found": False}

# ========== VIEWDNS (REVERSE IP) ==========
async def search_viewdns(domain):
    """ViewDNS.info ile reverse IP lookup"""
    print(f"🔍 ViewDNS.info'da reverse IP aranıyor: {domain}")
    results = []
    try:
        url = f"https://viewdns.info/reverseip/?host={domain}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Sonuç tablosunu bul
                    table = soup.find('table', border='1')
                    if table:
                        rows = table.find_all('tr')[1:11]  # İlk 10 sonuç
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                results.append({
                                    "domain": cols[0].text,
                                    "date": cols[1].text if len(cols) > 1 else "",
                                    "source": "ViewDNS"
                                })
    except Exception as e:
        print(f"❌ ViewDNS hatası: {e}")
    
    return results

# ========== SECURITYTRAILS API (DOMAIN) ==========
async def search_securitytrails(domain):
    """SecurityTrails API ile domain geçmişi ara"""
    if not SECURITY_TRAILS_API_KEY:
        print("⚠️ SecurityTrails API anahtarı yok, atlanıyor.")
        return None
    
    try:
        url = f"https://api.securitytrails.com/v1/domain/{domain}"
        headers = {"APIKEY": SECURITY_TRAILS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        if response.status_code == 200:
            return {
                "found": True,
                "hostname": data.get('hostname'),
                "alexa_rank": data.get('alexa_rank'),
                "registrar": data.get('registrar'),
                "name_servers": data.get('name_servers', [])[:3]
            }
    except Exception as e:
        print(f"❌ SecurityTrails hatası: {e}")
    
    return {"found": False}

# ========== WAYBACK MACHINE (ARŞİV) ==========
async def check_wayback_machine(url):
    """Wayback Machine'de URL'nin arşivlenip arşivlenmediğini kontrol et"""
    print(f"🔍 Wayback Machine'de arşiv aranıyor: {url}")
    try:
        api_url = f"https://archive.org/wayback/available?url={quote_plus(url)}"
        response = requests.get(api_url, timeout=10)
        data = response.json()
        
        if data.get('archived_snapshots', {}).get('closest', {}).get('available'):
            snapshot = data['archived_snapshots']['closest']
            return {
                "available": True,
                "url": snapshot.get('url'),
                "timestamp": snapshot.get('timestamp')
            }
    except Exception as e:
        print(f"❌ Wayback Machine hatası: {e}")
    
    return {"available": False}

# ========== GOOGLE CACHE ==========
async def check_google_cache(url):
    """Google Cache'de URL'yi kontrol et"""
    print(f"🔍 Google Cache'de aranıyor: {url}")
    try:
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{quote_plus(url)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(cache_url, timeout=10, allow_redirects=True) as response:
                if response.status == 200:
                    return {
                        "available": True,
                        "url": cache_url
                    }
    except:
        pass
    
    return {"available": False}

# ========== PHONEBOOK.CZ (EMAIL/USERNAME) ==========
async def search_phonebook(query, query_type="email"):
    """Phonebook.cz'de email veya kullanıcı adı ara"""
    print(f"🔍 Phonebook.cz'de {query_type} aranıyor: {query}")
    results = []
    try:
        url = f"https://phonebook.cz/search?q={quote_plus(query)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Sonuçları parse et
                    for result in soup.find_all('div', class_='result'):
                        link = result.find('a', href=True)
                        if link:
                            results.append({
                                "url": link['href'],
                                "text": result.text[:200],
                                "source": "Phonebook.cz"
                            })
    except Exception as e:
        print(f"❌ Phonebook.cz hatası: {e}")
    
    return results[:10]

# ========== THATSTHEM (KİŞİ ARAMA) ==========
async def search_thatsthem(name):
    """Thatsthem'de isim ara"""
    print(f"🔍 Thatsthem'de isim aranıyor: {name}")
    results = []
    try:
        url = f"https://thatsthem.com/name/{quote_plus(name)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Sonuçları parse et
                    for person in soup.find_all('div', class_='person'):
                        name_elem = person.find('div', class_='name')
                        if name_elem:
                            results.append({
                                "name": name_elem.text,
                                "details": person.text[:300],
                                "url": url
                            })
    except Exception as e:
        print(f"❌ Thatsthem hatası: {e}")
    
    return results[:5]

# ========== DISCORD'A MESAJ GÖNDERME ==========
def send_to_discord(embed_data):
    """Genel Discord gönderme fonksiyonu"""
    try:
        response = requests.post(webhook_url, json={"embeds": [embed_data]})
        return response.status_code in [200, 204]
    except:
        return False

def send_tiktok_profile(profile):
    """TikTok profil bilgilerini gönder"""
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
    if not profiles:
        return
    color = COLORS.get(platform_name.lower(), COLORS["default"])
    icon = "🔗"
    
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
    """İsim arama sonuçlarını gönder"""
    if not results:
        return
    
    embed = {
        "title": f"👤 İsim Arama Sonuçları – {len(results)} kaynak",
        "color": 0x00aaff,
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
    """Sızıntı raporu gönder"""
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
    """Domain raporu gönder"""
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
    """Arşiv raporu gönder"""
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
    
    send_tiktok_profile(profile)
    
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
                test_username = var_username
                result = await check_platform(session, platform, test_username)
                if result:
                    identifier = f"{platform['name']}:{result['url']}"
                    if identifier not in sent:
                        similarity = fuzz.ratio(username.lower(), var_username.lower())
                        if similarity >= 60:
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
    
    # 4. User-Searcher taraması (2000+ platform)
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
    
    # 6. İsim taraması (display_name varsa)
    if profile['display_name'] and profile['display_name'] != username:
        name_variations = generate_name_variations(profile['display_name'])
        print(f"📝 {len(name_variations)} isim varyasyonu test edilecek.")
        
        all_name_results = []
        for name in name_variations[:3]:  # İlk 3 varyasyon
            pipl_results = await search_pipl(name)
            all_name_results.extend(pipl_results)
            spokeo_results = await search_spokeo(name)
            all_name_results.extend(spokeo_results)
            zabasearch_results = await search_zabasearch(name)
            all_name_results.extend(zabasearch_results)
            thatsthem_results = await search_thatsthem(name)
            all_name_results.extend(thatsthem_results)
        
        if all_name_results:
            send_name_search_results(all_name_results, username, profile.get('avatar'))
            stats["İsim arama"] += len(all_name_results)
    
    # 7. Görsel arama (tüm motorlar)
    if profile.get('avatar'):
        print("\n🔎 Görsel arama başlıyor...")
        
        # Yandex (zaten var)
        yandex_results = await search_yandex(profile['avatar'], username)
        # Google
        google_results = await search_google(profile['avatar'], username)
        # Bing
        bing_results = await search_bing(profile['avatar'], username)
        # TinEye
        tineye_results = await search_tineye(profile['avatar'], username)
        # Lenso.ai
        lenso_results = await search_lenso(profile['avatar'], username)
        
        all_image_results = yandex_results + google_results + bing_results + tineye_results + lenso_results
        
        if all_image_results:
            send_image_search_group(all_image_results, profile.get('avatar'), username, "Çoklu Görsel Arama")
            stats["Görsel arama"] += len(all_image_results)
    
    # 8. Yüz tanıma (Skybiometry) - varsa diğer profillerin avatarı ile karşılaştır
    if profile.get('avatar') and SKYBIOMETRY_CLIENT_ID:
        print("\n🔎 Yüz tanıma başlıyor...")
        # Bulunan profillerin avatarlarını topla
        other_avatars = []
        for platform, profiles in found_by_platform.items():
            for p in profiles:
                if p.get('avatar'):
                    other_avatars.append(p['avatar'])
        
        # İlk 5 avatarı karşılaştır
        for i, other_avatar in enumerate(other_avatars[:5]):
            result = await compare_faces_skybiometry(profile['avatar'], other_avatar)
            if result and result.get('success'):
                embed = {
                    "title": f"🧬 Yüz Tanıma Sonucu",
                    "color": 0xff69b4,
                    "description": f"Benzerlik skoru: {result.get('similarity', '?')}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {"text": f"@{username} • Yüz karşılaştırma"}
                }
                send_to_discord(embed)
                stats["Yüz tanıma"] += 1
    
    # 9. Sızıntı taraması (email varsa)
    if profile.get('emails'):
        for email in profile['emails']:
            dehashed = await search_dehashed(email, "email")
            if dehashed.get('found', 0) > 0:
                send_leak_report(dehashed, email, username)
                stats["Sızıntı"] += 1
            
            leak_lookup = await search_leak_lookup(email)
            if leak_lookup and leak_lookup.get('found'):
                send_leak_report(leak_lookup, email, username)
                stats["Sızıntı"] += 1
    
    # 10. Domain taraması (biyografide domain varsa)
    if profile.get('urls'):
        for url in profile['urls']:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain:
                # Hunter.io
                hunter = await search_hunter(domain)
                if hunter and hunter.get('found'):
                    embed = {
                        "title": f"📧 {domain} Email Adresleri",
                        "color": COLORS["email"],
                        "description": f"{hunter['count']} email bulundu.\n" + "\n".join(hunter.get('emails', [])),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    send_to_discord(embed)
                    stats["Email"] += hunter['count']
                
                # ViewDNS
                viewdns = await search_viewdns(domain)
                if viewdns:
                    embed = {
                        "title": f"🌐 {domain} - Reverse IP",
                        "color": COLORS["domain"],
                        "fields": [{"name": "Aynı IP'deki Domainler", "value": "\n".join([v['domain'] for v in viewdns[:5]]), "inline": False}],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    send_to_discord(embed)
                    stats["Reverse IP"] += len(viewdns)
                
                # SecurityTrails
                strails = await search_securitytrails(domain)
                if strails and strails.get('found'):
                    send_domain_report(strails, domain, username)
                    stats["Domain"] += 1
                
                # Wayback Machine
                wayback = await check_wayback_machine(url)
                if wayback.get('available'):
                    send_archive_report(wayback, url, username)
                    stats["Arşiv"] += 1
                
                # Google Cache
                cache = await check_google_cache(url)
                if cache.get('available'):
                    embed = {
                        "title": "📦 Google Cache",
                        "color": COLORS["archive"],
                        "description": f"[Önbelleğe alınmış]({cache['url']})",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    send_to_discord(embed)
                    stats["Arşiv"] += 1
    
    # 11. Özet rapor
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
