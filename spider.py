import re
import asyncio
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def islink(content: str) -> list[str]: 
    '''抓出訊息中的所有網址並清理末端標點'''
    raw_links = re.findall(r'https?://[^\s>]+', content)
    return [re.sub(r'[.,!?)]+$', '', link) for link in raw_links]

def is_youtube_url(url: str) -> bool:
    '''判斷網址是否為 YouTube 連結（相容 www、m、shorts 及 youtu.be）'''
    pattern = r'^https?://(?:www\.|m\.)?(?:youtube\.com|youtu\.be)/'
    return bool(re.search(pattern, url))

def get_youtube_oembed(url: str) -> dict | None:
    '''YouTube 專用：透過 oEmbed API 抓取標題與頻道'''
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={quote(url)}&format=json"
        response = requests.get(oembed_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", "無標題"),
                "summary": f"頻道：{data.get('author_name', '未知')}"
            }
    except Exception as e:
        print(f"oEmbed 抓取失敗 ({url}): {e}")
    return None

def get_web_summary(url: str) -> dict | None:
    '''一般網站：透過 BeautifulSoup 解析 HTML'''
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.title.string.strip() if (soup.title and soup.title.string) else "無標題"
        meta_desc = (
            soup.find('meta', attrs={'name': 'description'}) or 
            soup.find('meta', attrs={'property': 'og:description'})
        )
        summary = meta_desc.get('content', '').strip() if meta_desc else "（無內文摘要）"

        return {
            "title": title,
            "summary": summary
        }
    except Exception as e:
        print(f"一般網頁抓取失敗 ({url}): {e}")
        return None

async def process_message_links(msg):
    word = msg.content
    links = islink(msg.content)
    
    if links:
        for link in set(links):
            # 依據網址類型自動分流
            if is_youtube_url(link):
                summary = await asyncio.to_thread(get_youtube_oembed, link)
                prefix = "YouTube 影片"
            else:
                summary = await asyncio.to_thread(get_web_summary, link)
                prefix = "網址"
            
            # 替換內文文字
            if summary:
                replacement = f'\n(一個{prefix}, 網址標題是: "{summary["title"]}", 內文摘要是: "{summary["summary"]}")'
                word = word.replace(link, replacement)
            else:
                word = word.replace(link, f'\n(一個{prefix}, 網址無法辨識)')

    return word