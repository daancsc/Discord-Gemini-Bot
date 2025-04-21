import requests
import urllib.parse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import isodate

load_dotenv()

APP_ID = os.getenv('WOLFRAMALPHA_APP_ID')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
url = "https://www.googleapis.com/customsearch/v1"

def google(s):
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": s,
    }

    response = requests.get(url, params=params)
    results = response.json()

    output = []

    for item in results.get("items", []):
        title = "標題： " + item["title"]
        about = "簡介： " + item.get("snippet", "")
        link  = "連結： " + item.get("link")
        output.append(f"{title}\n{about}\n{link}\n-----\n")

    return "搜尋結果: " + "\n".join(output) if output else "找不到任何結果"


def wolframalpha(query: str, query_or : str):
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.wolframalpha.com/v2/query?appid={APP_ID}&input={encoded_query}"

    response = requests.get(url)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        results = []

        for pod in root.findall(".//pod"):
            title = pod.attrib.get("title")
            texts = []
            for subpod in pod.findall("subpod"):
                plaintext = subpod.find("plaintext")
                if plaintext is not None and plaintext.text:
                    texts.append(plaintext.text.strip())

            if texts:
                # 把 title 和內容整理成一段段文字
                result_block = f"【{title}】\n" + "\n".join(texts)
                results.append(result_block)

        if results:
            return "\n\n".join(results)
        else:
            return "wolframalpha搜尋沒有結果，google搜尋結果如下" + google(query_or)
    else:
        return f"WolframAlpha 回傳錯誤：{response.status_code}"

def get_news(category):
    result = ""
    category_url = f"https://www.nownews.com/cat/{category}/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(category_url, headers=headers)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    left_col = soup.find("div", class_="leftCol")
    links = left_col.find_all("a", class_="trace-click")

    visited = set()
    count = 0

    for link in links:
        if count >= 5:
            break

        href = link.get("href")
        if href and href.startswith("https://www.nownews.com/news/") and href not in visited:
            visited.add(href)

            try:
                article_res = requests.get(href, headers=headers)
                article_res.encoding = "utf-8"
                article_soup = BeautifulSoup(article_res.text, "html.parser")

                title_tag = article_soup.find("h1", class_="article-title")
                title = title_tag.text.strip() if title_tag else "標題未找到"

                content_div = article_soup.find("div", id="articleContent")
                if content_div:
                    for ad in content_div.find_all(class_=["ad-blk", "ad-blk1"]):
                        ad.decompose()

                    for br in content_div.find_all("br"):
                        br.replace_with("\n")

                    text = content_div.get_text(strip=True, separator="\n")

                    # 移除 ▲ 開頭的整行
                    text = re.sub(r'^▲.*(?:\n|$)', '', text, flags=re.MULTILINE)
                    text = "\n".join([line for line in text.split("\n") if line.strip()])
                else:
                    text = "找不到文章內容"

                # 累加到結果字串
                result += f"📰 標題：{title}\n📄 內文：\n{text}\n\n{'='*10}\n\n"
                count += 1

            except Exception as e:
                print(f"⚠️ 無法處理 {href}：{e}")

    return result


async def youtube_search(query, max_results=5, language="en", duration="medium"):
    try:
        # 初始化 YouTube API 客戶端
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        # 設置搜尋參數
        search_params = {
            "part": "id,snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),  # API 限制最多 50 條
            "relevanceLanguage": language,
            "order": "relevance"  # 可改為 "viewCount" 或 "date"
        }

        # 篩選影片時長
        if duration in ["short", "medium", "long"]:
            search_params["videoDuration"] = duration

        # 執行搜尋請求
        request = youtube.search().list(**search_params)
        response = request.execute()

        # 提取影片 ID 清單
        video_ids = [item["id"]["videoId"] for item in response.get("items", [])]

        if not video_ids:
            return f"找不到與 '{query}' 相關的影片，請嘗試其他關鍵詞。"

        # 查詢影片詳細資訊（包括時長）
        details_request = youtube.videos().list(
            part="snippet,contentDetails",
            id=",".join(video_ids)
        )
        details_response = details_request.execute()

        # 格式化結果
        results = []
        for item in details_response.get("items", []):
            snippet = item["snippet"]
            content_details = item["contentDetails"]
            # 解析影片時長（ISO 8601 格式）
            duration = isodate.parse_duration(content_details["duration"])
            duration_str = f"{duration.seconds // 3600}h {duration.seconds % 3600 // 60}m" if duration.seconds >= 3600 else f"{duration.seconds // 60}m {duration.seconds % 60}s"
            # 解析發布日期
            published_at = datetime.strptime(snippet["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
            # 構建結果條目
            result = (
                f"[{snippet['title']}](https://www.youtube.com/watch?v={item['id']}) - "
                f"由 {snippet['channelTitle']} 發布，時長 {duration_str}，{published_at}"
            )
            results.append(result)

        # 返回格式化的清單
        return f"\n以下是 Youtube上 '{query}' 的搜尋結果：\n" + "\n".join(f"{i+1}. {result}" for i, result in enumerate(results))

    except HttpError as e:
        return f"YouTube API 請求失敗：{str(e)}"
    except Exception as e:
        return f"搜尋影片時發生錯誤：{str(e)}"