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
import json

load_dotenv()

APP_ID = os.getenv('WOLFRAMALPHA_APP_ID')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_ACCESS_TOKEN = os.getenv('TMDB_ACCESS_TOKEN')
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

def tmdb_search(query, media_type='movie', language='zh-TW', year=None, include_adult=False):
    """
    使用TMDB API搜尋電影或電視節目
    
    參數:
    - query: 搜尋關鍵字
    - media_type: 'movie'或'tv'
    - language: 語言代碼 (例如: 'zh-TW')
    - year: 發行年份 (可選)
    - include_adult: 是否包含成人內容
    
    返回格式化的搜尋結果
    """
    base_url = "https://api.themoviedb.org/3"
    
    # 設定不同media_type的搜索端點
    if media_type in ['movie', 'tv']:
        search_url = f"{base_url}/search/{media_type}"
    else:
        # 如果是人物或其他，使用multi搜索
        search_url = f"{base_url}/search/multi"
        
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': language,
        'include_adult': include_adult
    }
    
    # 如果指定了年份且是電影搜索，添加年份篩選
    if year and media_type == 'movie':
        params['year'] = year
        
    # 設定請求頭，包含授權權杖
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送搜索請求
        response = requests.get(search_url, params=params, headers=headers)
        response.raise_for_status()  # 檢查是否有HTTP錯誤
        results = response.json().get('results', [])
        
        if not results:
            return f"找不到與「{query}」相關的{media_type_name(media_type)}，請嘗試其他關鍵詞。"
            
        # 格式化搜索結果
        formatted_results = []
        
        for item in results[:5]:  # 限制顯示前5項結果
            # 根據媒體類型獲取相應的信息
            if media_type == 'movie' or item.get('media_type') == 'movie':
                title = item.get('title', '未知標題')
                release_date = item.get('release_date', '未知日期')
                item_type = "電影"
                date_prefix = "上映日期"
            elif media_type == 'tv' or item.get('media_type') == 'tv':
                title = item.get('name', '未知標題')
                release_date = item.get('first_air_date', '未知日期')
                item_type = "電視劇"
                date_prefix = "首播日期"
            elif item.get('media_type') == 'person':
                title = item.get('name', '未知名稱')
                known_for = ", ".join([i.get('title', i.get('name', '未知')) for i in item.get('known_for', [])])
                formatted_results.append(f"🎭 {title} - 知名作品: {known_for}")
                continue
            else:
                continue
                
            # 獲取評分
            vote_average = item.get('vote_average', 0)
            # 獲取概述，如果太長則截斷
            overview = item.get('overview', '')
            if not overview.strip():
                overview = '無概述'
            elif len(overview) > 150:
                overview = overview[:150] + '...'
                
            # 格式化並添加結果
            formatted_results.append(
                f"🎬 {item_type}：{title}\n"
                f"⭐ 評分：{vote_average}/10\n"
                f"📅 {date_prefix}：{release_date}\n"
                f"📝 概述：{overview}\n"
                f"🔗 連結：https://www.themoviedb.org/{media_type}/{item.get('id')}"
            )
            
        # 返回格式化的結果
        return f"以下是關於「{query}」的{media_type_name(media_type)}搜尋結果：\n\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.HTTPError as e:
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"搜尋{media_type_name(media_type)}時發生錯誤：{str(e)}"

def tmdb_discover(media_type='movie', language='zh-TW', sort_by='popularity.desc', year=None, 
                  with_genres=None, vote_average_gte=None, with_keywords=None, include_adult=False):
    """
    使用TMDB的discover API根據過濾條件找到電影或電視節目
    
    參數:
    - media_type: 'movie'或'tv'
    - language: 語言代碼 (例如: 'zh-TW')
    - sort_by: 排序方式 (例如: 'popularity.desc', 'vote_average.desc', 'release_date.desc')
    - year: 發行年份 (僅電影)
    - with_genres: 類型ID (例如: '28' 對應動作片)
    - vote_average_gte: 最低評分 (例如: 7)
    - with_keywords: 關鍵詞ID
    - include_adult: 是否包含成人內容
    
    返回格式化的過濾結果
    """
    base_url = "https://api.themoviedb.org/3"
    discover_url = f"{base_url}/discover/{media_type}"
    
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'language': language,
        'sort_by': sort_by,
        'include_adult': include_adult,
        'page': 1
    }
    
    # 添加可選參數
    if year:
        if media_type == 'movie':
            params['primary_release_year'] = year
        else:
            params['first_air_date_year'] = year
            
    if with_genres:
        params['with_genres'] = with_genres
        
    if vote_average_gte:
        params['vote_average.gte'] = vote_average_gte
        
    if with_keywords:
        params['with_keywords'] = with_keywords
    
    # 設定請求頭，包含授權權杖
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送請求
        response = requests.get(discover_url, params=params, headers=headers)
        response.raise_for_status()
        results = response.json().get('results', [])
        
        if not results:
            return f"根據指定條件找不到{media_type_name(media_type)}，請嘗試其他條件。"
            
        # 格式化結果
        formatted_results = []
        
        for item in results[:8]:  # 限制顯示前8項
            if media_type == 'movie':
                title = item.get('title', '未知標題')
                release_date = item.get('release_date', '未知日期')
                item_type = "電影"
                date_prefix = "上映日期"
            else:
                title = item.get('name', '未知標題')
                release_date = item.get('first_air_date', '未知日期')
                item_type = "電視劇"
                date_prefix = "首播日期"
                
            # 獲取評分
            vote_average = item.get('vote_average', 0)
            # 獲取概述，如果太長則截斷
            overview = item.get('overview', '')
            if not overview.strip():
                overview = '無概述'
            elif len(overview) > 150:
                overview = overview[:150] + '...'
                
            # 格式化並添加結果
            formatted_results.append(
                f"🎬 {item_type}：{title}\n"
                f"⭐ 評分：{vote_average}/10\n"
                f"📅 {date_prefix}：{release_date}\n"
                f"📝 概述：{overview}\n"
                f"🔗 連結：https://www.themoviedb.org/{media_type}/{item.get('id')}"
            )
            
        # 返回格式化的結果
        sort_description = sort_by_description(sort_by)
        filter_description = ""
        if with_genres:
            filter_description += f"、類型篩選"
        if vote_average_gte:
            filter_description += f"、最低評分{vote_average_gte}分"
        if year:
            filter_description += f"、{year}年發行"
            
        return f"以下是{sort_description}{filter_description}的{media_type_name(media_type)}：\n\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.HTTPError as e:
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"使用過濾條件搜尋{media_type_name(media_type)}時發生錯誤：{str(e)}"

def sort_by_description(sort_by):
    """將排序方式轉換為中文描述"""
    descriptions = {
        'popularity.desc': '最受歡迎',
        'popularity.asc': '最冷門',
        'vote_average.desc': '評分最高',
        'vote_average.asc': '評分最低',
        'release_date.desc': '最新發行',
        'release_date.asc': '最早發行',
        'revenue.desc': '票房最高',
        'primary_release_date.desc': '最新發行',
        'primary_release_date.asc': '最早發行',
    }
    return descriptions.get(sort_by, '符合條件')

def tmdb_find(external_id, external_source, language='zh-TW'):
    """
    使用外部ID在TMDB中查找電影、電視劇或人物
    
    參數:
    - external_id: 外部ID (例如: IMDB ID)
    - external_source: 外部資料源類型 (例如: 'imdb_id', 'tvdb_id')
    - language: 語言代碼 (例如: 'zh-TW')
    
    返回格式化的查找結果
    """
    base_url = "https://api.themoviedb.org/3"
    find_url = f"{base_url}/find/{external_id}"
    
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'language': language,
        'external_source': external_source
    }
    
    # 設定請求頭
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送請求
        response = requests.get(find_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 檢查所有可能的結果類型
        result_types = [
            ('movie_results', '電影', 'movie'), 
            ('tv_results', '電視劇', 'tv'),
            ('person_results', '人物', 'person'),
            ('tv_episode_results', '電視劇集', 'tv_episode'),
            ('tv_season_results', '電視季度', 'tv_season')
        ]
        
        all_results = []
        
        for result_key, type_name, type_id in result_types:
            results = data.get(result_key, [])
            if results:
                for item in results:
                    if type_id == 'movie':
                        title = item.get('title', '未知標題')
                        release_date = item.get('release_date', '未知日期')
                        id_val = item.get('id')
                        all_results.append(
                            f"🎬 {type_name}：{title}\n"
                            f"⭐ 評分：{item.get('vote_average', 0)}/10\n"
                            f"📅 上映日期：{release_date}\n"
                            f"🔗 連結：https://www.themoviedb.org/{type_id}/{id_val}"
                        )
                    elif type_id == 'tv':
                        title = item.get('name', '未知標題')
                        first_air_date = item.get('first_air_date', '未知日期')
                        id_val = item.get('id')
                        all_results.append(
                            f"📺 {type_name}：{title}\n"
                            f"⭐ 評分：{item.get('vote_average', 0)}/10\n"
                            f"📅 首播日期：{first_air_date}\n"
                            f"🔗 連結：https://www.themoviedb.org/{type_id}/{id_val}"
                        )
                    elif type_id == 'person':
                        name = item.get('name', '未知名稱')
                        id_val = item.get('id')
                        known_for = ", ".join([i.get('title', i.get('name', '未知')) 
                                            for i in item.get('known_for', [])][:3])
                        all_results.append(
                            f"🎭 {type_name}：{name}\n"
                            f"✨ 知名作品：{known_for}\n"
                            f"🔗 連結：https://www.themoviedb.org/{type_id}/{id_val}"
                        )
                    elif type_id in ['tv_episode', 'tv_season']:
                        name = item.get('name', '未知名稱')
                        show_id = item.get('show_id')
                        season_number = item.get('season_number')
                        episode_number = item.get('episode_number', '')
                        
                        url_path = f"tv/{show_id}"
                        if type_id == 'tv_season':
                            url_path += f"/season/{season_number}"
                        elif type_id == 'tv_episode':
                            url_path += f"/season/{season_number}/episode/{episode_number}"
                            
                        all_results.append(
                            f"📺 {type_name}：{name}\n"
                            f"🔗 連結：https://www.themoviedb.org/{url_path}"
                        )
        
        if not all_results:
            return f"找不到外部ID為 {external_id} 的資料，請確認ID和資料源類型是否正確。"
            
        # 返回格式化的結果
        source_name = external_source_name(external_source)
        return f"以下是使用{source_name} ID「{external_id}」找到的結果：\n\n" + "\n\n".join(all_results)
        
    except requests.exceptions.HTTPError as e:
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"使用外部ID查找時發生錯誤：{str(e)}"

def external_source_name(external_source):
    """將外部資料源類型轉換為中文名稱"""
    names = {
        'imdb_id': 'IMDB',
        'freebase_mid': 'Freebase',
        'freebase_id': 'Freebase',
        'tvdb_id': 'TVDB',
        'tvrage_id': 'TVRage',
        'facebook_id': 'Facebook',
        'twitter_id': 'Twitter',
        'instagram_id': 'Instagram'
    }
    return names.get(external_source, external_source)

def tmdb_rated_list(account_id, media_type='tv', language='zh-TW', session_id=None, sort_by='created_at.desc'):
    """
    獲取用戶評分過的電影或電視節目清單
    
    參數:
    - account_id: TMDB帳戶ID
    - media_type: 'tv'或'movies'
    - language: 語言代碼 (例如: 'zh-TW')
    - session_id: 會話ID (如果需要)
    - sort_by: 排序方式 ('created_at.asc' 或 'created_at.desc')
    
    返回格式化的評分清單
    """
    base_url = "https://api.themoviedb.org/3"
    rated_url = f"{base_url}/account/{account_id}/rated/{media_type}"
    
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'language': language,
        'sort_by': sort_by,
        'page': 1
    }
    
    if session_id:
        params['session_id'] = session_id
    
    # 設定請求頭
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送請求
        response = requests.get(rated_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            return f"找不到用戶評分過的{media_type_name(media_type)}，請確認帳戶ID和會話ID是否正確。"
            
        # 格式化結果
        formatted_results = []
        
        for item in results[:10]:  # 限制顯示前10項
            if media_type == 'movies':
                title = item.get('title', '未知標題')
                release_date = item.get('release_date', '未知日期')
                item_type = "電影"
                date_prefix = "上映日期"
                url_type = "movie"
            else:
                title = item.get('name', '未知標題')
                release_date = item.get('first_air_date', '未知日期')
                item_type = "電視劇"
                date_prefix = "首播日期"
                url_type = "tv"
                
            # 獲取用戶評分
            user_rating = item.get('rating', 0)
            # 獲取平均評分
            vote_average = item.get('vote_average', 0)
                
            # 格式化並添加結果
            formatted_results.append(
                f"🎬 {item_type}：{title}\n"
                f"⭐ 用戶評分：{user_rating}/10\n"
                f"👥 平均評分：{vote_average}/10\n"
                f"📅 {date_prefix}：{release_date}\n"
                f"🔗 連結：https://www.themoviedb.org/{url_type}/{item.get('id')}"
            )
            
        # 返回格式化的結果
        sort_text = "最早" if sort_by == 'created_at.asc' else "最近"
        return f"用戶ID {account_id} {sort_text}評分的{media_type_name(media_type)}：\n\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return f"獲取評分清單失敗：未授權，請確認您的API金鑰和會話ID是否有效。"
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"獲取用戶評分清單時發生錯誤：{str(e)}"

def tmdb_now_playing(language='zh-TW', page=1, region=None):
    """
    獲取當前正在上映的電影
    
    參數:
    - language: 語言代碼 (例如: 'zh-TW')
    - page: 頁碼
    - region: ISO-3166-1國家/地區代碼 (可選)
    
    返回格式化的電影列表
    """
    base_url = "https://api.themoviedb.org/3"
    endpoint_url = f"{base_url}/movie/now_playing"
    
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'language': language,
        'page': page
    }
    
    if region:
        params['region'] = region
    
    # 設定請求頭
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送請求
        response = requests.get(endpoint_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        dates = data.get('dates', {})
        
        if not results:
            return f"目前沒有正在上映的電影資訊。"
        
        # 格式化結果
        formatted_results = []
        
        for movie in results[:8]:  # 限制顯示前8部
            title = movie.get('title', '未知標題')
            release_date = movie.get('release_date', '未知日期')
            vote_average = movie.get('vote_average', 0)
            overview = movie.get('overview', '')
            
            # 如果概述太長則截斷
            if not overview.strip():
                overview = '無概述'
            elif len(overview) > 150:
                overview = overview[:150] + '...'
            
            # 格式化並添加結果
            formatted_results.append(
                f"🎬 電影：{title}\n"
                f"⭐ 評分：{vote_average}/10\n"
                f"📅 上映日期：{release_date}\n"
                f"📝 概述：{overview}\n"
                f"🔗 連結：https://www.themoviedb.org/movie/{movie.get('id')}"
            )
        
        # 顯示日期範圍
        date_info = ""
        if dates:
            min_date = dates.get('minimum', '')
            max_date = dates.get('maximum', '')
            if min_date and max_date:
                date_info = f"（{min_date} 至 {max_date}）"
        
        # 返回格式化的結果
        region_text = f"在{region}地區" if region else ""
        total_results = data.get('total_results', 0)
        return f"目前{region_text}正在上映的電影{date_info}，共有{total_results}部，以下是其中幾部：\n\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.HTTPError as e:
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"獲取當前上映電影時發生錯誤：{str(e)}"

def tmdb_upcoming(language='zh-TW', page=1, region=None):
    """
    獲取即將上映的電影
    
    參數:
    - language: 語言代碼 (例如: 'zh-TW')
    - page: 頁碼
    - region: ISO-3166-1國家/地區代碼 (可選)
    
    返回格式化的電影列表
    """
    base_url = "https://api.themoviedb.org/3"
    endpoint_url = f"{base_url}/movie/upcoming"
    
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'language': language,
        'page': page
    }
    
    if region:
        params['region'] = region
    
    # 設定請求頭
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送請求
        response = requests.get(endpoint_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        dates = data.get('dates', {})
        
        if not results:
            return f"目前沒有即將上映的電影資訊。"
        
        # 格式化結果
        formatted_results = []
        
        for movie in results[:8]:  # 限制顯示前8部
            title = movie.get('title', '未知標題')
            release_date = movie.get('release_date', '未知日期')
            vote_average = movie.get('vote_average', 0)
            overview = movie.get('overview', '')
            
            # 如果概述太長則截斷
            if not overview.strip():
                overview = '無概述'
            elif len(overview) > 150:
                overview = overview[:150] + '...'
            
            # 格式化並添加結果
            formatted_results.append(
                f"🎬 電影：{title}\n"
                f"⭐ 評分：{vote_average}/10\n"
                f"📅 上映日期：{release_date}\n"
                f"📝 概述：{overview}\n"
                f"🔗 連結：https://www.themoviedb.org/movie/{movie.get('id')}"
            )
        
        # 顯示日期範圍
        date_info = ""
        if dates:
            min_date = dates.get('minimum', '')
            max_date = dates.get('maximum', '')
            if min_date and max_date:
                date_info = f"（{min_date} 至 {max_date}）"
        
        # 返回格式化的結果
        region_text = f"在{region}地區" if region else ""
        total_results = data.get('total_results', 0)
        return f"即將{region_text}上映的電影{date_info}，共有{total_results}部，以下是其中幾部：\n\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.HTTPError as e:
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"獲取即將上映電影時發生錯誤：{str(e)}"

def tmdb_popular(language='zh-TW', page=1, region=None):
    """
    獲取熱門電影
    
    參數:
    - language: 語言代碼 (例如: 'zh-TW')
    - page: 頁碼
    - region: ISO-3166-1國家/地區代碼 (可選)
    
    返回格式化的電影列表
    """
    base_url = "https://api.themoviedb.org/3"
    endpoint_url = f"{base_url}/movie/popular"
    
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'language': language,
        'page': page
    }
    
    if region:
        params['region'] = region
    
    # 設定請求頭
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送請求
        response = requests.get(endpoint_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        
        if not results:
            return f"無法獲取熱門電影資訊。"
        
        # 格式化結果
        formatted_results = []
        
        for movie in results[:8]:  # 限制顯示前8部
            title = movie.get('title', '未知標題')
            release_date = movie.get('release_date', '未知日期')
            vote_average = movie.get('vote_average', 0)
            popularity = movie.get('popularity', 0)
            overview = movie.get('overview', '')
            
            # 如果概述太長則截斷
            if not overview.strip():
                overview = '無概述'
            elif len(overview) > 150:
                overview = overview[:150] + '...'
            
            # 格式化並添加結果
            formatted_results.append(
                f"🎬 電影：{title}\n"
                f"⭐ 評分：{vote_average}/10\n"
                f"🔥 人氣指數：{popularity}\n"
                f"📅 上映日期：{release_date}\n"
                f"📝 概述：{overview}\n"
                f"🔗 連結：https://www.themoviedb.org/movie/{movie.get('id')}"
            )
        
        # 返回格式化的結果
        region_text = f"在{region}地區" if region else ""
        total_results = data.get('total_results', 0)
        return f"目前{region_text}最熱門的電影，共有{total_results}部，以下是排名前幾的電影：\n\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.HTTPError as e:
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"獲取熱門電影時發生錯誤：{str(e)}"

def tmdb_top_rated(language='zh-TW', page=1, region=None):
    """
    獲取評分最高的電影
    
    參數:
    - language: 語言代碼 (例如: 'zh-TW')
    - page: 頁碼
    - region: ISO-3166-1國家/地區代碼 (可選)
    
    返回格式化的電影列表
    """
    base_url = "https://api.themoviedb.org/3"
    endpoint_url = f"{base_url}/movie/top_rated"
    
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'language': language,
        'page': page
    }
    
    if region:
        params['region'] = region
    
    # 設定請求頭
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送請求
        response = requests.get(endpoint_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        
        if not results:
            return f"無法獲取評分最高的電影資訊。"
        
        # 格式化結果
        formatted_results = []
        
        for movie in results[:8]:  # 限制顯示前8部
            title = movie.get('title', '未知標題')
            release_date = movie.get('release_date', '未知日期')
            vote_average = movie.get('vote_average', 0)
            vote_count = movie.get('vote_count', 0)
            overview = movie.get('overview', '')
            
            # 如果概述太長則截斷
            if not overview.strip():
                overview = '無概述'
            elif len(overview) > 150:
                overview = overview[:150] + '...'
            
            # 格式化並添加結果
            formatted_results.append(
                f"🎬 電影：{title}\n"
                f"⭐ 評分：{vote_average}/10 (共{vote_count}個評分)\n"
                f"📅 上映日期：{release_date}\n"
                f"📝 概述：{overview}\n"
                f"🔗 連結：https://www.themoviedb.org/movie/{movie.get('id')}"
            )
        
        # 返回格式化的結果
        region_text = f"在{region}地區" if region else ""
        total_results = data.get('total_results', 0)
        return f"評分{region_text}最高的電影，共有{total_results}部，以下是排名前幾的電影：\n\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.HTTPError as e:
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"獲取評分最高電影時發生錯誤：{str(e)}"

def media_type_name(media_type):
    """將媒體類型轉換為中文名稱"""
    names = {
        'movie': '電影',
        'tv': '電視節目',
        'multi': '影視作品',
        'person': '人物'
    }
    return names.get(media_type, '影視作品')

def time_window_name(time_window):
    """將時間窗口轉換為中文名稱"""
    names = {
        'day': '日',
        'week': '週'
    }
    return names.get(time_window, '週')

def tmdb_trending(media_type='all', time_window='week', language='zh-TW'):
    """
    獲取TMDB趨勢內容
    
    參數:
    - media_type: 'all', 'movie', 'tv', 或 'person'
    - time_window: 'day' 或 'week'
    - language: 語言代碼 (例如: 'zh-TW')
    
    返回格式化的趨勢列表
    """
    base_url = "https://api.themoviedb.org/3"
    trend_url = f"{base_url}/trending/{media_type}/{time_window}"
    
    # 準備請求參數
    params = {
        'api_key': TMDB_API_KEY,
        'language': language
    }
    
    # 設定請求頭
    headers = {
        'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
        'Content-Type': 'application/json;charset=utf-8'
    }
    
    try:
        # 發送請求
        response = requests.get(trend_url, params=params, headers=headers)
        response.raise_for_status()
        results = response.json().get('results', [])
        
        if not results:
            return f"目前無法獲取{time_window_name(time_window)}趨勢{media_type_name(media_type)}。"
            
        # 格式化結果
        formatted_results = []
        
        for i, item in enumerate(results[:8], 1):  # 限制顯示前8項，並提供排名
            # 根據媒體類型獲取相應的信息
            if (media_type == 'all' and item.get('media_type') == 'person') or media_type == 'person':
                name = item.get('name', '未知名稱')
                known_for = ", ".join([i.get('title', i.get('name', '未知')) for i in item.get('known_for', [])])
                popularity = item.get('popularity', 0)
                item_type = "人物"
                
                # 格式化人物結果
                formatted_results.append(
                    f"🎭 {item_type}：{name}\n"
                    f"🥇 人氣排名：{i}\n"
                    f"🔥 人氣指數：{popularity}\n"
                    f"🎬 知名作品：{known_for}\n"
                    f"🔗 連結：https://www.themoviedb.org/person/{item.get('id')}"
                )
                continue
                
            # 電影或電視劇
            if (media_type == 'all' and item.get('media_type') == 'movie') or media_type == 'movie':
                title = item.get('title', '未知標題')
                release_date = item.get('release_date', '未知日期')
                item_type = "電影"
                date_prefix = "上映日期"
                media_url = "movie"
            else:
                title = item.get('name', '未知標題')
                release_date = item.get('first_air_date', '未知日期')
                item_type = "電視劇"
                date_prefix = "首播日期"
                media_url = "tv"
                
            # 獲取評分
            vote_average = item.get('vote_average', 0)
            
            # 獲取概述並處理
            overview = item.get('overview', '')
            if not overview.strip():
                overview = '無概述'
            elif len(overview) > 150:
                overview = overview[:150] + '...'
                
            # 格式化電影或電視劇結果
            formatted_results.append(
                f"🔥 {item_type}：{title}\n"
                f"⭐ 評分：{vote_average}/10\n"
                f"📅 {date_prefix}：{release_date}\n"
                f"📝 概述：{overview}\n"
                f"🔗 連結：https://www.themoviedb.org/{media_url}/{item.get('id')}"
            )
        
        # 返回格式化的結果
        return f"{time_window_name(time_window)}趨勢{media_type_name(media_type)}：\n\n" + "\n\n".join(formatted_results)
        
    except requests.exceptions.HTTPError as e:
        return f"TMDB API請求失敗，HTTP錯誤：{str(e)}"
    except Exception as e:
        return f"獲取趨勢{media_type_name(media_type)}時發生錯誤：{str(e)}"