print("🚀 BOT BAŞLADI!")

import os
import asyncio
import requests
import re
import time
from datetime import datetime
from playwright.async_api import async_playwright

# Playwright Stealth (isteğe bağlı)
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("⚠️ playwright-stealth kurulu değil, devam ediliyor.")

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

async def get_tiktok_data(username):
    print(f"🔍 TikTok kullanıcısı: @{username}")
    async with async_playwright() as p:
        # Firefox kullan (daha az engellenir)
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        if STEALTH_AVAILABLE:
            await stealth_async(page)
            print("✅ Stealth uygulandı")

        # Profil sayfasına git
        profile_url = f"https://www.tiktok.com/@{username}"
        print(f"🌐 Gidilen URL: {profile_url}")
        try:
            await page.goto(profile_url, timeout=60000)
            print("✅ Sayfa yüklendi")
        except Exception as e:
            print(f"❌ Sayfa yüklenemedi: {e}")
            await browser.close()
            return None, [], []

        # Sayfanın yüklenmesi için bekle
        print("⏳ Sayfa yükleniyor...")
        await page.wait_for_timeout(20000)  # 20 saniye bekle

        # ----- PROFİL BİLGİLERİ -----
        profile_data = {}

        # Profil fotoğrafı (geliştirilmiş seçiciler)
        avatar_selectors = [
            'img[src*="avt"]',
            'img[alt*="avatar"]',
            'img[class*="avatar"]',
            'img[data-e2e="user-avatar"]',
            'img[src*="tos-alisg-avt"]'  # verdiğin linkteki pattern
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
        if not avatar:
            print("⚠️ Profil fotoğrafı bulunamadı")

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

        # ----- VİDEOLAR SEKMESİNE TIKLA VE VİDEO LİNKLERİNİ TOPLA -----
        video_links = []

        # "Videolar" sekmesini bul (data-e2e="videos-tab")
        try:
            videos_tab = await page.query_selector('div[data-e2e="videos-tab"]')
            if videos_tab:
                print("✅ Videolar sekmesi bulundu, tıklanıyor...")
                await videos_tab.click()
                await page.wait_for_timeout(5000)
            else:
                print("⚠️ Videolar sekmesi bulunamadı, sayfa zaten videolar sekmesinde olabilir.")
        except Exception as e:
            print(f"⚠️ Videolar sekmesine tıklanamadı: {e}")

        # Sayfayı kaydırarak video yükle
        print("📜 Sayfa kaydırılıyor (video yüklemek için)...")
        for _ in range(8):  # 8 kez kaydır
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await page.wait_for_timeout(3000)

        # Tüm linkleri al
        all_links = await page.eval_on_selector_all(
            'a[href]',
            'els => els.map(el => el.href)'
        )
        print(f"🔗 Toplam link sayısı: {len(all_links)}")

        # Debug: İlk 20 linki yazdır (ne tür linkler var görmek için)
        print("📎 İlk 20 link örneği:")
        for i, link in enumerate(all_links[:20]):
            print(f"   {i+1}. {link[:100]}")

        # Video linklerini filtrele (içinde /video/ geçenler)
        video_links = [link for link in all_links if '/video/' in link]
        video_links = list(set(video_links))[:10]
        print(f"🎥 Video linkleri (/{'video/'} içeren): {len(video_links)}")

        # Eğer hala 0'sa, regex ile dene
        if len(video_links) == 0:
            content = await page.content()
            video_ids = re.findall(r'/video/(\d+)', content)
            unique_ids = list(set(video_ids))[:10]
            if unique_ids:
                regex_links = [f"https://www.tiktok.com/@{username}/video/{vid}" for vid in unique_ids]
                video_links = regex_links
                print(f"🎥 Regex ile {len(video_links)} video linki oluşturuldu")

        # ----- REPOST SEKMESİNE TIKLA VE REPOST LİNKLERİNİ TOPLA -----
        repost_links = []

        # "Repost" sekmesini bul (data-e2e="repost-tab")
        try:
            repost_tab = await page.query_selector('div[data-e2e="repost-tab"]')
            if repost_tab:
                print("✅ Repost sekmesi bulundu, tıklanıyor...")
                await repost_tab.click()
                await page.wait_for_timeout(8000)

                # Sayfayı kaydır
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(3000)

                # Linkleri topla
                repost_all = await page.eval_on_selector_all(
                    'a[href]',
                    'els => els.map(el => el.href)'
                )
                repost_links = [link for link in repost_all if '/video/' in link]
                repost_links = list(set(repost_links))[:10]
                print(f"🔄 Repost linkleri: {len(repost_links)}")
            else:
                print("⚠️ Repost sekmesi bulunamadı.")
        except Exception as e:
            print(f"⚠️ Repost sekmesine tıklama hatası: {e}")

        # Eğer repost sekmesi yoksa alternatif URL'leri dene
        if not repost_links:
            print("⚠️ Repost sekmesi bulunamadı, alternatif URL'ler deneniyor...")
            alt_urls = [
                f"https://www.tiktok.com/@{username}?lang=en#repost",
                f"https://www.tiktok.com/@{username}/repost",
                f"https://www.tiktok.com/@{username}?lang=en"
            ]
            for url in alt_urls:
                print(f"🌐 {url} deneniyor...")
                try:
                    await page.goto(url, timeout=60000)
                    await page.wait_for_timeout(15000)
                    for _ in range(5):
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                        await page.wait_for_timeout(3000)
                    repost_all = await page.eval_on_selector_all(
                        'a[href]',
                        'els => els.map(el => el.href)'
                    )
                    repost_links = [link for link in repost_all if '/video/' in link]
                    repost_links = list(set(repost_links))[:10]
                    if repost_links:
                        print(f"🔄 {url} adresinde {len(repost_links)} repost bulundu")
                        break
                except Exception as e:
                    print(f"⚠️ Hata: {e}")

        await browser.close()
        return profile_data, video_links, repost_links

def send_profile_to_discord(profile_data, username):
    print("📤 Profil bilgileri Discord'a gönderiliyor...")
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
        response = requests.post(os.environ["DISCORD_WEBHOOK"], json={"embeds": [embed]})
        print(f"📨 Profil gönderme cevabı: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Profil gönderme hatası: {e}")
        return False

def send_videos_to_discord(video_links, username, video_type="video"):
    if not video_links:
        return 0
    title = "🎥 Kendi Videoları" if video_type == "video" else "🔄 Repost Videoları"
    color = 0x00ff00 if video_type == "video" else 0xffaa00
    print(f"📤 {len(video_links)} {title} gönderiliyor...")
    gonderilen = 0
    for link in video_links:
        embed = {
            "title": title,
            "url": link,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"@{username} • {video_type}"}
        }
        try:
            response = requests.post(os.environ["DISCORD_WEBHOOK"], json={"embeds": [embed]})
            if response.status_code in [200, 204]:
                gonderilen += 1
                print(f"✅ Gönderildi: {link[:50]}...")
            else:
                print(f"⚠️ Hata: {response.status_code}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Gönderme hatası: {e}")
    return gonderilen

async def main():
    username = os.environ["TIKTOK_USER"]
    sent_videos_file = "sent_videos.txt"
    sent_reposts_file = "sent_reposts.txt"

    try:
        with open(sent_videos_file, "r") as f:
            sent_videos = set(f.read().splitlines())
        print(f"📁 Daha önce gönderilen video sayısı: {len(sent_videos)}")
    except:
        sent_videos = set()
        print("📁 sent_videos.txt dosyası bulunamadı")

    try:
        with open(sent_reposts_file, "r") as f:
            sent_reposts = set(f.read().splitlines())
        print(f"📁 Daha önce gönderilen repost sayısı: {len(sent_reposts)}")
    except:
        sent_reposts = set()
        print("📁 sent_reposts.txt dosyası bulunamadı")

    profile_sent_file = "profile_sent.txt"
    try:
        with open(profile_sent_file, "r") as f:
            profile_sent = f.read().strip() == username
    except:
        profile_sent = False

    profile_data, video_links, repost_links = await get_tiktok_data(username)

    if not profile_data:
        print("❌ Profil verileri alınamadı, işlem iptal.")
        return

    if not profile_sent:
        print("🆕 Profil bilgileri ilk kez gönderiliyor...")
        if send_profile_to_discord(profile_data, username):
            with open(profile_sent_file, "w") as f:
                f.write(username)
            await asyncio.sleep(2)
    else:
        print("⏩ Profil daha önce gönderilmiş.")

    print(f"\n📊 İşlenecek video sayısı: {len(video_links)}")
    yeni_videolar = [link for link in video_links if link not in sent_videos]
    if yeni_videolar:
        print(f"🆕 {len(yeni_videolar)} yeni video bulundu")
        gonderilen = send_videos_to_discord(yeni_videolar, username, "video")
        for link in yeni_videolar:
            sent_videos.add(link)
        with open(sent_videos_file, "w") as f:
            f.write("\n".join(sent_videos))
        print(f"✅ {gonderilen} yeni video gönderildi.")
    else:
        print("⏩ Yeni video yok.")

    print(f"\n📊 İşlenecek repost sayısı: {len(repost_links)}")
    yeni_repostlar = [link for link in repost_links if link not in sent_reposts]
    if yeni_repostlar:
        print(f"🆕 {len(yeni_repostlar)} yeni repost bulundu")
        gonderilen = send_videos_to_discord(yeni_repostlar, username, "repost")
        for link in yeni_repostlar:
            sent_reposts.add(link)
        with open(sent_reposts_file, "w") as f:
            f.write("\n".join(sent_reposts))
        print(f"✅ {gonderilen} yeni repost gönderildi.")
    else:
        print("⏩ Yeni repost yok.")

    print("\n✅ Bot çalışması tamamlandı.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print("❌ HATA OLUŞTU!")
        print(traceback.format_exc())
