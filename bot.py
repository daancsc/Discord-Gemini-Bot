import discord
import time
import aiohttp
from discord.ext import commands
import google.generativeai as genai
import aiohttp
import json
import os
import aiofiles
from datetime import datetime
from dotenv import load_dotenv
from spider import islink,gettitle
from tools import wolframalpha,get_news,youtube_search,load_memory,get_current_time

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
bot_token = os.getenv('BOT_TOKEN')


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all()) # 設定 Discord bot

genai.configure(api_key = api_key) #記得放入自己的api key

generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "max_output_tokens": 2048,
  "response_mime_type": "text/plain",
}

safety_settings = [
    {
        'category': 'HARM_CATEGORY_HARASSMENT',
        'threshold': 'block_none'
    },
    {
        'category': 'HARM_CATEGORY_HATE_SPEECH',
        'threshold': 'block_none'
    },
    {
        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
        'threshold': 'block_none'
    },
    {
        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
        'threshold': 'block_none'
    },
]

model = genai.GenerativeModel(
  model_name="gemini-3.5-flash-lite",
  generation_config=generation_config,
  safety_settings = safety_settings
)

image_model = genai.GenerativeModel(
    model_name='gemini-3.5-flash-lite', 
    generation_config=generation_config) # 定義另外一個 model 用來生成圖片回應 (兩者不能相容)

pool_file = "pool.json"
message_history = []
with open("prompt.txt", "r", encoding="utf-8") as f:
    prompt = f.read()

# 定義一個函式來方便呼叫api
async def call_api(msg):
    chat_session = model.start_chat(history=[
    ])

    if not msg: return '這段訊息是空的'

    await chat_session.send_message_async(msg) # 傳送 msg 內容給 Gemini api
    return chat_session.last.text # 將 api 的回應返還給主程式

#圖片辨識
async def image_api(image_data):
    image_parts = [{'mime_type': 'image/jpeg', 'data': image_data}]

    # (下) 如果 text 不為空, 就用 text 依據文字內容來生成回應, 如果為空, 就依據 '這張圖片代表什麼?給我更多細節' 來生成回應
    prompt_parts = [image_parts[0], "這張圖片代表什麼? 請詳細描述這張圖片有些什麼元素"]
    response = image_model.generate_content(prompt_parts)

    if response._error: return '無法分析這張圖'

    return response.text

# 上傳對話紀錄
async def update_history(msg):
    message_history.append(msg)

    if len(message_history) > 200:
        message_history.pop(0)

    # 每 50 條就觸發 call_api 並寫入 pool.json
    if len(message_history) >= 50 and len(message_history) % 50 == 0:
        response = await call_api(
            prompt + 
            "\n".join(message_history[-50:]) + 
            f"\n=====\n當前時間是{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n以上是使用者與你的對話紀錄，請用自然語言，客觀的總結出對話(不要使用json格式)的主要內容與重點，並且需提及使用者 ID（而非名稱）和時間，用於未來對話中作為參考，以建立長期記憶。")
        await save_to_pool(response)
        print("\n已整理記憶\n" + response + "\n")
        message_history = message_history[-10:]

    return "\n".join(message_history)


async def save_to_pool(response):
    # 確保 pool.json 存在並是 list 格式
    if os.path.exists(pool_file):
        with open(pool_file, "r", encoding="utf-8") as f:
            try:
                pool_data = json.load(f)
            except json.JSONDecodeError:
                pool_data = []
    else:
        pool_data = []

    pool_data.append(response)

    with open(pool_file, "w", encoding="utf-8") as f:
        json.dump(pool_data, f, ensure_ascii=False, indent=2)

def extract_json_block(text):
    """
    從文字中尋找並解析第一個合法的 JSON 區塊（支援巢狀），
    返回 (解析後的 JSON 物件, 起始位置, 結束位置) 或 None。
    """
    start = text.find("{")
    while start != -1:
        stack = []
        for i in range(start, len(text)):
            if text[i] == "{":
                stack.append("{")
            elif text[i] == "}":
                if stack:
                    stack.pop()
                if not stack:  # 找到完整的 JSON 區塊
                    json_str = text[start:i+1]
                    try:
                        parsed_json = json.loads(json_str)
                        return parsed_json, start, i + 1
                    except json.JSONDecodeError:
                        break  # JSON 格式錯誤，換下一組
        start = text.find("{", start + 1)
    return None, -1, -1

async def process_tools_in_response(response: str) -> str:
    print("原始回應：", response)
    all_tool_outputs = []  # 儲存所有工具的執行結果
    processed_jsons = set()  # 記錄已處理的 JSON 字符串，避免重複
    max_iterations = 20  # 限制最大迭代次數，防止無限循環

    iteration = 0
    while iteration < max_iterations:
        data, start, end = extract_json_block(response)
        if not data:
            print("未找到新的 JSON 區塊，結束提取")
            break

        # 將 JSON 轉為字符串，用於檢查是否已處理
        json_str = json.dumps(data, sort_keys=True)
        if json_str in processed_jsons:
            print(f"檢測到重複的 JSON 區塊：{json_str}，跳過")
            # 移除重複的 JSON 區塊，防止下次循環再次提取
            response = response[:start] + response[end:]
            iteration += 1
            continue

        tool_response = None
        if data.get("type") == "wolframalpha" and data.get("question_original") and data.get("question_english"):
            print(f"正在使用 wolframalpha，內容原文:{data["question_original"]}，內容英文:{data["question_english"]}")
            tool_response = wolframalpha(data["question_english"], data["question_original"])

        elif data.get("type") == "get_news" and data.get("category"):
            print(f"正在使用 get_news，類別：{data['category']}")
            tool_response = get_news(data["category"])

        elif data.get("type") == "youtube_search" and data.get("query") and data.get("max_results") and data.get("language") and data.get("duration"):
            print(f"正在使用 youtube_search，內容：{data['query']}")
            tool_response = await youtube_search(data["query"], int(data["max_results"]), data["language"], data["duration"])

        elif data.get("type") == "load_memory" and data.get("amount"):
            print(f"正在使用 get_memory，內容：{data['amount']}")
            tool_response = await load_memory(data["amount"])

        elif data.get("type") == "get_current_time":
            print("正在使用 get_current_time")
            tool_response = get_current_time()

        # 移除當前 JSON 區塊（無論是否有有效工具回應）
        response = response[:start] + response[end:]
        print("移除 JSON 後的回應：", response)

        if tool_response:
            print("工具結果：", tool_response)
            all_tool_outputs.append(tool_response)
            processed_jsons.add(json_str)  # 記錄已處理的 JSON
        else:
            print(f"無效工具或缺少參數，跳過 JSON：{json_str}")
            processed_jsons.add(json_str)  # 即使無效也要記錄，避免重複處理

        iteration += 1

    # 如果有工具結果，則一次性送回模型處理
    if all_tool_outputs:
        print("所有工具結果：", all_tool_outputs)
        # 將工具結果合併到系統提示中，並明確要求模型不要生成新的工具 JSON
        history = await update_history(
            "[system]: (模型已調用外部工具，結果如下，請根據結果回應使用者的問題，並避免生成新的工具 JSON 區塊)\n" +
            "\n".join(all_tool_outputs)
        )
        response = await call_api(prompt + history)
        await update_history("[model]: " + response)
    else:
        print("無工具結果，直接返回原始回應")

    return response

@bot.event
async def on_ready():
    print(f'bot on ready！')

# 延遲測試指令
@bot.command(name='ping')
async def ping(ctx):
    start = time.perf_counter()
    message = await ctx.send('Pong！')
    end = time.perf_counter()
    await message.edit(content=f'Pong！延遲 {round((end - start) * 1000)} ms (API 往返) | 閘道 {round(bot.latency * 1000)} ms')


# on_message事件
@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    await bot.process_commands(msg)
    if msg.content.startswith(bot.command_prefix):
        return

    async with msg.channel.typing():
        attachment_info = None  # 儲存附件資訊（圖片描述或文字檔內容）

        # 處理圖片或文字檔附件
        if msg.attachments:
            for attachment in msg.attachments:
                filename = attachment.filename.lower()

                # 圖片處理
                if any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status != 200:
                                await msg.reply('圖片載入失敗。', mention_author=False)
                                return

                            print(f'正在分析使用者的圖片...')
                            image_data = await resp.read()
                            response_text = await image_api(image_data)
                            print(f'使用者的圖片內容:{response_text}')
                            attachment_info = f"(附上一張圖片，內容是「{response_text}」)"

                # 純文字檔案處理
                elif any(filename.endswith(ext) for ext in ['.txt', '.md', '.log']):
                    file_path = f"temp_{msg.id}_{filename}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status != 200:
                                await msg.reply('文字檔案載入失敗。', mention_author=False)
                                return
                            
                            f = await aiofiles.open(file_path, mode='wb')
                            await f.write(await resp.read())
                            await f.close()

                    try:
                        f = await aiofiles.open(file_path, mode='r', encoding='utf-8', errors='ignore')
                        text_data = await f.read()
                        await f.close()

                        print(f'使用者上傳的文字檔內容:\n{text_data[:500]}')
                        attachment_info = f"(附上一個文字檔，內容是「{text_data[:300]}...」)"
                    finally:
                        if os.path.exists(file_path):
                            os.remove(file_path)

        # 重設對話指令
        global message_history
        if msg.content.lower() == "reset":
            message_history = []
            await msg.channel.send("對話紀錄已清除")
            return

        # 處理文字與網址
        word = msg.content
        links = islink(msg.content)
        if links:
            for link in links:
                title = gettitle(link)
                word = word.replace(link, f'(一個網址, 網址標題是: "{title}")\n' if title else '(一個網址, 網址無法辨識)\n')

        if attachment_info:
            word += f"\n{attachment_info}"

        roles = [role.name for role in msg.author.roles if role != msg.guild.default_role]
        history = await update_history(f"[{msg.author.display_name}(id: {msg.author.id}, 身分組:{', '.join(roles)})]: {word}")
        print("訊息內容:", word)

        response = await call_api(prompt + history)
        await update_history("[model]: " + response)
        response = await process_tools_in_response(response)
        await msg.reply(response.replace("[model]:", ""))
        print(response)

#在本地執行
# ================
bot.run(bot_token)
# ================
