import os
import json
import logging
import asyncio
import requests
from config import *
from pyrogram import Client, enums
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)

SKYMOVIESHD_URL = "https://skymovieshd.video/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

MOVIES_FILE = "data/movies.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(MOVIES_FILE):
    with open(MOVIES_FILE, "w") as f:
        json.dump([], f)

def load_posted_movies():
    try:
        with open(MOVIES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] 

def save_posted_movies(movies):
    with open(MOVIES_FILE, "w") as f:
        json.dump(movies, f, indent=4)

async def extract_download_links(movie_url):
    try:
        response = requests.get(movie_url, headers=HEADERS)
        if response.status_code != 200:
            logging.error(f"Failed to load movie page {movie_url} (Status Code: {response.status_code})")
            return None        
        soup = BeautifulSoup(response.text, 'html.parser')
        title_section = soup.select_one('div[class^="Robiul"]')
        movie_title = title_section.text.replace('Download ', '').strip() if title_section else "Unknown Title"
        _cache = set()
        hubcloud_links = []        
        for link in soup.select('a[href*="howblogs.xyz"]'):
            href = link['href']
            if href in _cache:
                continue
            _cache.add(href)
            resp = requests.get(href, headers=HEADERS)
            nsoup = BeautifulSoup(resp.text, 'html.parser')
            atag = nsoup.select('div[class="cotent-box"] > a[href]')
            for dl_link in atag:
                hubcloud_url = dl_link['href']
                if "hubcloud" in hubcloud_url:
                    hubcloud_links.append(hubcloud_url)
        if not hubcloud_links:
            logging.warning(f"No HubCloud links found for {movie_url}")
            return None
        direct_links = await get_direct_hubcloud_link(hubcloud_links[0])
        if not direct_links:
            return None
        return direct_links
    except Exception as e:
        logging.error(f"Error extracting download links from {movie_url}: {e}")
        return None

async def get_direct_hubcloud_link(hubcloud_url, max_retries=5):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
        )
        page = await browser.new_page()
        try:
            logging.info(f"🖇️ Opening {hubcloud_url}...")
            await page.goto(hubcloud_url, wait_until="domcontentloaded", timeout=30000)
            logging.info("✅ Page is fully loaded.")

            retries = 0
            file_name = "Unknown File"

            try:
                file_name_element = await page.query_selector("div.card-header")
                if file_name_element:
                    file_name = await file_name_element.inner_text()
                    logging.info(f"📁 Extracted File Name: {file_name}")
            except Exception as e:
                logging.warning(f"⚠️ File name not found: {e}")

            while retries < max_retries:
                current_url = page.url
                logging.info(f"📌 Current URL: {current_url}")

                if "hubcloud" in current_url:
                    try:
                        logging.info("🔍 Searching for 'Download' Button...")
                        download_button = await page.query_selector("a#download")
                        if download_button:
                            logging.info("✅ Found 'Download' Button. Clicking...")
                            await download_button.click()
                            await page.wait_for_load_state("domcontentloaded", timeout=20000)
                        else:
                            logging.warning("⚠️ Download button not found!")
                            retries += 1
                            continue
                    except Exception as e:
                        logging.warning(f"⚠️ Download button not found: {e}")
                        retries += 1
                        continue

                try:
                    final_buttons = await page.query_selector_all("a.btn")
                    final_links = [
                        await btn.get_attribute("href")
                        for btn in final_buttons
                        if "Download [FSL Server]" in await btn.inner_text() or "Download [PixelServer : 2]" in await btn.inner_text()
                    ]
                    if final_links:
                        logging.info(f"✅ Extracted Direct Download Links: {final_links}")
                        return {"file_name": file_name, "download_links": final_links}
                    else:
                        logging.warning("⚠️ No valid download buttons found!")
                        retries += 1
                        await page.go_back()
                        continue
                except Exception as e:
                    logging.warning(f"⚠️ Error extracting final links: {e}")

                retries += 1
            logging.error("❌ Max retries reached. Skipping this URL.")
            return {"file_name": file_name, "download_links": []}
        except Exception as e:
            logging.error(f"❌ Error processing {hubcloud_url}: {e}")
            return {"file_name": "Unknown File", "download_links": []}
        finally:
            await browser.close()

async def scrape_skymovieshd(client):
    posted_movies = load_posted_movies() 
    movies = get_movie_links()     
    for movie in movies:
        if movie['title'] in posted_movies:
            logging.info(f"⏩ Skipping {movie['title']} (Already Posted)")
            continue 
        logging.info(f"🔍 Processing: {movie['title']}")
        direct_links = await extract_download_links(movie['link'])
        if not direct_links:
            logging.warning(f"⚠️ No Valid Download Links Found For {movie['title']}.")
            continue
        message = f"<b>Recently Posted Movie ✅</b>\n\n<b>{movie['title']}</b>\n\n<b>Download Links:</b>\n\n"
        for data in direct_links:
            if isinstance(data, dict) and "file_name" in data and "download_links" in data:
                file_name = data["file_name"]
                download_links = data["download_links"]
                message += f"<b>{file_name}</b>\n"
                message += "\n".join([f"{i}. {link}" for i, link in enumerate(download_links, start=1)]) + "\n\n"
        try:
            await client.send_message(chat_id=CHANNEL_ID, text=message, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
            logging.info(f"✅ Posted: {movie['title']}")
            posted_movies.append(movie['title'])
            save_posted_movies(posted_movies)
        except Exception as e:
            logging.error(f"❌ Failed To Post {movie['title']}: {e}")
        await asyncio.sleep(3)

async def check_new_movies(client):
    while True:
        logging.info("Checking for new movies...")
        await scrape_skymovieshd(client) 
        await asyncio.sleep(CHECK_INTERVAL)
