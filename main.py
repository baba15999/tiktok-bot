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

# ========== PLATFORM LİSTESİ (gelişmiş doğrulama ile) ==========
PLATFORMS = [
    {
        "name": "Instagram",
        "url": "https://www.instagram.com/{}",
        "icon": "📸",
        "check_method": "html",
        "not_found_patterns": ["Sayfa Bulunamadı", "Page Not Found", "Hesap mevcut değil", "Sorry, this page isn't available"],
        "success_patterns": ["profilePage", "instagram.com/"]
    },
    {
        "name": "Twitter",
        "url": "https://twitter.com/{}",
        "icon": "🐦",
        "check_method": "html",
        "not_found_patterns": ["Bu hesap mevcut değil", "This account doesn’t exist", "Hesap askıya alındı"],
        "success_patterns": ["data-testid", "twitter.com/"]
    },
    {
        "name": "Facebook",
        "url": "https://www.facebook.com/{}",
        "icon": "📘",
        "check_method": "html",
        "not_found_patterns": ["Bu içerik şu anda mevcut değil", "Sayfa Bulunamadı"],
        "success_patterns": ["profile.php", "facebook.com/"]
    },
    {
        "name": "YouTube",
        "url": "https://www.youtube.com/@{}",
        "icon": "🎥",
        "check_method": "html",
        "not_found_patterns": ["Bu kanal mevcut değil", "This channel doesn't exist"],
        "success_patterns": ["channel_id", "youtube.com/@"]
    },
    {
        "name": "Twitch",
        "url": "https://www.twitch.tv/{}",
        "icon": "🎮",
        "check_method": "html",
        "not_found_patterns": ["Sorry. Unless you’ve got a time machine", "Üzgünüz, aradığınız sayfayı bulamadık"],
        "success_patterns": ["twitch.tv/"]
    },
    {
        "name": "Reddit",
        "url": "https://www.reddit.com/user/{}",
        "icon": "👽",
        "check_method": "html",
        "not_found_patterns": ["Sorry, nobody on Reddit goes by that name", "Böyle bir kullanıcı yok"],
        "success_patterns": ["reddit.com/user/"]
    },
    {
        "name": "GitHub",
        "url": "https://github.com/{}",
        "icon": "🐙",
        "check_method": "html",
        "not_found_patterns": ["404", "Page not found"],
        "success_patterns": ["github.com/"]
    },
    {
        "name": "Pinterest",
        "url": "https://www.pinterest.com/{}",
        "icon": "📌",
        "check_method": "html",
        "not_found_patterns": ["Hata", "Sorry, we couldn't find that page"],
        "success_patterns": ["pinterest.com/"]
    },
    {
        "name": "Tumblr",
        "url": "https://{}.tumblr.com",
        "icon": "📝",
        "check_method": "html",
        "not_found_patterns": ["There's nothing here", "Burada hiçbir şey yok"],
        "success_patterns": ["tumblr.com"]
    },
    {
        "name": "Snapchat",
        "url": "https://www.snapchat.com/add/{}",
        "icon": "👻",
        "check_method": "redirect",
        "not_found_patterns": [],
        "success_patterns": []
    },
    {
        "name": "Telegram",
        "url": "https://t.me/{}",
        "icon": "✈️",
        "check_method": "html",
        "not_found_patterns": ["Sorry, this username doesn't exist", "Bu kullanıcı adı mevcut değil"],
        "success_patterns": ["telegram.me"]
    },
    {
        "name": "LinkedIn",
        "url": "https://www.linkedin.com/in/{}",
        "icon": "💼",
        "check_method": "html",
        "not_found_patterns": ["Page Not Found", "Sayfa Bulunamadı"],
        "success_patterns": ["linkedin.com/in/"]
    },
    {
        "name": "TikTok (farklı hesap)",
        "url": "https://www.tiktok.com/@{}",
        "icon": "🎵",
        "check_method": "html",
        "not_found_patterns": ["Couldn't find this account", "Bu hesap bulunamadı"],
        "success_patterns": ["tiktok.com/@"]
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

# ========== KULLANICI ADI VARYASYONLARI (akıllı sıralama) ==========
def generate_username_variations(username):
    """Farklı kullanıcı adı varyasyonları üret, en mantıklıları önce gelecek şekilde sırala"""
    variations = []
    
    # Orijinal
    variations.append((username, 100))  # (username, priority)
    
    # Büyük-küçük harf
    variations.append((username.lower(), 99))
    variations.append((username.upper(), 80))
    variations.append((username.capitalize(), 95))
    
    # Nokta ekleme (a.r.a.s.i)
    if len(username) > 3:
        dotted = '.'.join(username)
        variations.append((dotted, 85))
    
    # Tire ekleme
    dashed = '-'.join(username)
    variations.append((dashed, 84))
    
    # Alt çizgi ekleme
    underscored = '_'.join(username)
    variations.append((underscored, 83))
    
    # Sayı ekleme (en yaygın)
    for i in range(1, 4):
        variations.append((f"{username}{i}", 90 - i))
        variations.append((f"{username}_{i}", 89 - i))
        variations.append((f"{username}-{i}", 88 - i))
    
    # Kısaltma
    if len(username) > 5:
        variations.append((username[:int(len(username)/2)], 70))
    
    # Benzersiz yap ve önceliğe göre sırala
    unique = {}
    for u, p in variations:
        if u not in unique or p > unique[u]:
            unique[u] = p
    
    # Önceliğe göre sıralanmış liste
    sorted_vars = sorted(unique.items(), key=lambda x: x[1], reverse=True)
    return [v[0] for v in sorted_vars[:20]]  # Max 20 varyasyon

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
        avatar = None
        try:
            avatar = await page.eval_on_selector('img[src*="avt"]', 'el => el.src')
        except:
            pass
        
        # İsim
        try:
            display_name = await page.eval_on_selector('h1[data-e2e="user-title"]', 'el => el.textContent')
            display_name = display_name.strip()
        except:
            display_name = username
        
        # Takipçi/Takip
        followers = following = "?"
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
            "display_name": display_name,
            "followers": followers,
            "following": following,
            "bio": bio,
            "username": username
        }

# ========== AKILLI PLATFORM KONTROLÜ ==========
async def check_platform(session, platform, username):
    """Bir platformda kullanıcı adını kontrol et, gerçekten var mı yok mu doğrula"""
    url = platform["url"].format(username)
    try:
        async with session.get(url, timeout=15, allow_redirects=True, ssl=False) as response:
            # Önce HTTP durumuna bak
            if response.status != 200:
                return None
            
            # Sayfa içeriğini al
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            page_title = soup.find('title').text if soup.find('title') else ""
            
            # Platforma özel doğrulama
            not_found = False
            
            # 1. Title'da "not found" vb. ara
            not_found_patterns = platform.get("not_found_patterns", [])
            for pattern in not_found_patterns:
                if pattern.lower() in page_title.lower() or pattern.lower() in html.lower():
                    not_found = True
                    break
            
            # 2. Bazı platformlarda özel element kontrolü
            if platform["name"] == "Instagram":
                # Instagram'da profil yoksa body'de belirli bir class olur
                if 'x1e56ztr' not in html and 'profilePage' not in html:
                    not_found = True
            
            elif platform["name"] == "Twitter":
                if 'data-testid' not in html and 'error' in page_title.lower():
                    not_found = True
            
            if not_found:
                return None
            
            # Profil bilgilerini topla
            profile_info = {
                "url": str(response.url),
                "title": page_title[:150],
                "description": "",
                "avatar": None,
                "followers": None
            }
            
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                profile_info["description"] = meta_desc.get('content', '')[:200]
            
            # Open graph image
            og_image = soup.find('meta', property='og:image')
            if og_image:
                profile_info["avatar"] = og_image.get('content', '')
            
            # Platforma özel ekstra bilgiler
            if platform["name"] == "Instagram":
                # Takipçi sayısını bulmaya çalış
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
async def search_image_multi_engine(image_url, tiktok_username):
    """Çoklu görsel arama motorlarında ara, sadece sosyal medya linklerini döndür"""
    print(f"🔍 Çoklu görsel arama başlıyor...")
    all_results = []
    
    # Yandex
    yandex_results = await search_yandex(image_url, tiktok_username)
    all_results.extend(yandex_results)
    
    # Google (basit)
    google_results = await search_google(image_url, tiktok_username)
    all_results.extend(google_results)
    
    # Bing
    bing_results = await search_bing(image_url, tiktok_username)
    all_results.extend(bing_results)
    
    # Benzersiz ve sosyal medya linklerini filtrele
    social_pattern = re.compile(r'(instagram\.com|twitter\.com|facebook\.com|tiktok\.com|youtube\.com|twitch\.tv|reddit\.com|github\.com)')
    filtered = []
    seen = set()
    
    for res in all_results:
        url = res['url']
        if social_pattern.search(url) and url not in seen:
            seen.add(url)
            filtered.append(res)
    
    return filtered[:15]  # Max 15 sonuç

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

# ========== DISCORD'A GRUPLANMIŞ MESAJ GÖNDERME ==========
def send_platform_group(platform_name, profiles, tiktok_avatar, tiktok_user):
    """Aynı platformda bulunan tüm profilleri tek bir embed'de liste olarak gönder"""
    if not profiles:
        return
    
    color = COLORS.get(platform_name.lower(), COLORS["default"])
    icon = next((p["icon"] for p in PLATFORMS if p["name"] == platform_name), "🔗")
    
    # En yüksek benzerliğe göre sırala
    profiles.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Alanları oluştur
    fields = []
    for p in profiles[:5]:  # En fazla 5 tane göster
        name = f"@{p['username']} (benzerlik %{p['similarity']})"
        value = f"[Profili görüntüle]({p['url']})"
        if p.get('followers'):
            value += f" | 👥 {p['followers']} takipçi"
        fields.append({"name": name, "value": value, "inline": False})
    
    # Eğer 5'ten fazla varsa, kalan sayısını belirt
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
        print(f"📤 {platform_name} için {len(profiles)} profil gönderildi (gruplanmış).")
    except Exception as e:
        print(f"❌ Grup gönderme hatası: {e}")
    time.sleep(1)

def send_image_search_group(results, tiktok_avatar, tiktok_user):
    """Görsel arama sonuçlarını tek bir embed'de grupla"""
    if not results:
        return
    
    fields = []
    for res in results[:8]:  # İlk 8 sonuç
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
        print(f"📤 Görsel arama sonuçları gönderildi (gruplanmış).")
    except Exception as e:
        print(f"❌ Görsel arama gönderme hatası: {e}")
    time.sleep(1)

def send_summary_report(found_counts, tiktok_user):
    """Tarama özetini gönder"""
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
    
    # Daha önce gönderilen profilleri takip et (tüm platformlar için tek dosya)
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
    
    # TikTok profilini gönder (her zaman gönder)
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
    
    # 2. Kullanıcı adı varyasyonları oluştur
    variations = generate_username_variations(username)
    print(f"📝 {len(variations)} kullanıcı adı varyasyonu test edilecek.")
    
    # Bulunan profilleri platforma göre grupla
    found_by_platform = defaultdict(list)
    
    # 3. Tüm varyasyonları tüm platformlarda dene
    async with aiohttp.ClientSession() as session:
        for var_username in variations:
            print(f"\n🔎 Test ediliyor: '{var_username}'")
            
            for platform in PLATFORMS:
                # Platform özel format (Tumblr için farklı)
                test_username = var_username
                if platform["name"] == "Tumblr":
                    test_username = var_username  # zaten format {}.tumblr.com
                
                result = await check_platform(session, platform, test_username)
                
                if result:
                    # Profil gerçekten var
                    identifier = f"{platform['name']}:{result['url']}"
                    
                    if identifier not in sent:
                        # Benzerlik hesapla
                        similarity = fuzz.ratio(username.lower(), var_username.lower())
                        
                        # Sadece benzerlik %70'in üzerindeyse ekle (spam önleme)
                        if similarity >= 60:  # Eşik değeri
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
                    
                    # Rate limit koruması
                    await asyncio.sleep(1.5)
            
            await asyncio.sleep(1)  # Varyasyonlar arası bekle
    
    # 4. Gruplanmış platform raporlarını gönder
    platform_counts = {}
    for platform_name, profiles in found_by_platform.items():
        if profiles:
            send_platform_group(platform_name, profiles, profile.get('avatar'), username)
            platform_counts[platform_name] = len(profiles)
    
    # 5. Görsel arama (profil fotoğrafı varsa)
    if profile.get('avatar'):
        print("\n🔎 Görsel arama başlıyor...")
        image_results = await search_image_multi_engine(profile['avatar'], username)
        if image_results:
            send_image_search_group(image_results, profile.get('avatar'), username)
    
    # 6. Özet rapor
    if platform_counts:
        send_summary_report(platform_counts, username)
    
    # Gönderilenleri kaydet
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
