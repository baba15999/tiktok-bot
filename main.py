print("🚀 FEDAI BOT PRO BAŞLADI!")

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
    {
        "name": "Instagram",
        "url": "https://www.instagram.com/{}",
        "icon": "📸",
        "check_method": "html"
    },
    {
        "name": "Twitter",
        "url": "https://twitter.com/{}",
        "icon": "🐦",
        "check_method": "html"
    },
    {
        "name": "Facebook",
        "url": "https://www.facebook.com/{}",
        "icon": "📘",
        "check_method": "html"
    },
    {
        "name": "YouTube",
        "url": "https://www.youtube.com/@{}",
        "icon": "🎥",
        "check_method": "html"
    },
    {
        "name": "Twitch",
        "url": "https://www.twitch.tv/{}",
        "icon": "🎮",
        "check_method": "html"
    },
    {
        "name": "Reddit",
        "url": "https://www.reddit.com/user/{}",
        "icon": "👽",
        "check_method": "html"
    },
    {
        "name": "GitHub",
        "url": "https://github.com/{}",
        "icon": "🐙",
        "check_method": "html"
    },
    {
        "name": "Pinterest",
        "url": "https://www.pinterest.com/{}",
        "icon": "📌",
        "check_method": "html"
    },
    {
        "name": "Tumblr",
        "url": "https://{}.tumblr.com",
        "icon": "📝",
        "check_method": "html"
    },
    {
        "name": "Snapchat",
        "url": "https://www.snapchat.com/add/{}",
        "icon": "👻",
        "check_method": "redirect"
    },
    {
        "name": "Telegram",
        "url": "https://t.me/{}",
        "icon": "✈️",
        "check_method": "html"
    },
    {
        "name": "LinkedIn",
        "url": "https://www.linkedin.com/in/{}",
        "icon": "💼",
        "check_method": "html"
    },
    {
        "name": "TikTok (farklı hesap)",
        "url": "https://www.tiktok.com/@{}",
        "icon": "🎵",
        "check_method": "html"
    },
]

# ========== TEST MESAJI ==========
test_embed = {
    "title": "🧪 FEDAI BOT PRO AKTİF",
    "description": f"TikTok kullanıcısı: @{tiktok_user}\nDetaylı akıllı tarama başlıyor...",
    "color": 0x00ff00
}
try:
    r = requests.post(webhook_url, json={"embeds": [test_embed]})
    print(f"📨 TEST MESAJI GÖNDERİLDİ: {r.status_code}")
except Exception as e:
    print(f"❌ TEST MESAJI HATASI: {e}")

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
        return {
            "avatar": avatar,
            "display_name": display_name,
            "followers": followers,
            "following": following,
            "bio": bio,
            "username": username
        }

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
    results = []
    try:
        search_url = f"https://www.google.com/searchbyimage?image_url={quote_plus(image_url)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
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

async def search_image_multi_engine(image_url, tiktok_username):
    print(f"🔍 Çoklu görsel arama başlıyor...")
    all_results = []
    yandex_results = await search_yandex(image_url, tiktok_username)
    all_results.extend(yandex_results)
    google_results = await search_google(image_url, tiktok_username)
    all_results.extend(google_results)
    bing_results = await search_bing(image_url, tiktok_username)
    all_results.extend(bing_results)
    
    social_pattern = re.compile(r'(instagram\.com|twitter\.com|facebook\.com|tiktok\.com|youtube\.com|twitch\.tv|reddit\.com|github\.com)')
    filtered = []
    seen = set()
    for res in all_results:
        url = res['url']
        if social_pattern.search(url) and url not in seen:
            seen.add(url)
            filtered.append(res)
    return filtered[:15]

# ========== DISCORD'A GRUPLANMIŞ MESAJ GÖNDERME ==========
def send_platform_group(platform_name, profiles, tiktok_avatar, tiktok_user):
    if not profiles:
        return
    color = COLORS.get(platform_name.lower(), COLORS["default"])
    icon = next((p["icon"] for p in PLATFORMS if p["name"] == platform_name), "🔗")
    
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
    
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
        print(f"📤 {platform_name} için {len(profiles)} profil gönderildi.")
    except Exception as e:
        print(f"❌ Grup gönderme hatası: {e}")
    time.sleep(1)

def send_image_search_group(results, tiktok_avatar, tiktok_user):
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
        "title": f"🖼️ Görsel Arama Sonuçları – {len(results)} bağlantı",
        "color": 0xffaa00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Görsel benzerliği"},
        "fields": fields
    }
    if tiktok_avatar:
        embed["thumbnail"] = {"url": tiktok_avatar}
    
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
        print(f"📤 Görsel arama sonuçları gönderildi.")
    except Exception as e:
        print(f"❌ Görsel arama gönderme hatası: {e}")
    time.sleep(1)

def send_summary_report(found_counts, tiktok_user):
    if not found_counts:
        return
    total = sum(found_counts.values())
    description = f"Toplam **{total}** profil bulundu.\n"
    for platform, count in found_counts.items():
        description += f"\n{platform}: {count}"
    
    embed = {
        "title": "📊 Tarama Raporu",
        "description": description,
        "color": 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": f"@{tiktok_user} • Akıllı tarama tamamlandı"}
    }
    try:
        requests.post(webhook_url, json={"embeds": [embed]})
    except Exception as e:
        print(f"❌ Rapor gönderme hatası: {e}")

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
    
    # TikTok profil embed
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
    try:
        requests.post(webhook_url, json={"embeds": [embed_profile]})
        time.sleep(2)
    except:
        pass
    
    variations = generate_username_variations(username)
    print(f"📝 {len(variations)} kullanıcı adı varyasyonu test edilecek.")
    
    found_by_platform = defaultdict(list)
    
    async with aiohttp.ClientSession() as session:
        for var_username in variations:
            print(f"\n🔎 Test ediliyor: '{var_username}'")
            for platform in PLATFORMS:
                test_username = var_username
                if platform["name"] == "Tumblr":
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
                                "title": result.get('title'),
                                "avatar": result.get('avatar')
                            })
                            sent.add(identifier)
                            print(f"✅ {platform['name']}: {var_username} (benzerlik %{similarity})")
                    await asyncio.sleep(1.5)
            await asyncio.sleep(1)
    
    platform_counts = {}
    for platform_name, profiles in found_by_platform.items():
        if profiles:
            send_platform_group(platform_name, profiles, profile.get('avatar'), username)
            platform_counts[platform_name] = len(profiles)
    
    if profile.get('avatar'):
        print("\n🔎 Görsel arama başlıyor...")
        image_results = await search_image_multi_engine(profile['avatar'], username)
        if image_results:
            send_image_search_group(image_results, profile.get('avatar'), username)
    
    if platform_counts:
        send_summary_report(platform_counts, username)
    
    with open(sent_file, "w") as f:
        f.write("\n".join(sent))
    
    print(f"\n✅ Bot çalışması tamamlandı. {sum(platform_counts.values())} yeni profil bulundu.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
