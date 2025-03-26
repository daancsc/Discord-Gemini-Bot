import os
from dotenv import load_dotenv
import discord
import aiohttp
from discord.ext import commands
import google.generativeai as genai
from spider import islink,gettitle

load_dotenv()

api_key = os.getenv('API_KEY')
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
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  safety_settings = safety_settings
)

image_model = genai.GenerativeModel(
    model_name='gemini-1.5-pro', 
    generation_config=generation_config) # 定義另外一個 model 用來生成圖片回應 (兩者不能相容)


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
async def image_api(image_data, text):
    image_parts = [{'mime_type': 'image/jpeg', 'data': image_data}]

    # (下) 如果 text 不為空, 就用 text 依據文字內容來生成回應, 如果為空, 就依據 '這張圖片代表什麼?給我更多細節' 來生成回應
    prompt_parts = [image_parts[0], f'\n{text if text else "這張圖片代表什麼? 請描述這張圖片有些什麼元素"}']
    response = image_model.generate_content(prompt_parts)

    if response._error: return '無法分析這張圖'

    return response.text

# 上傳對話紀錄
async def update_history(msg):
    message_history.append(msg)
    if len(message_history) > 200:
        message_history.pop(0)
    return "\n".join(message_history)

@bot.event
async def on_ready():
    print(f'bot on ready！')


# on_message事件
@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    if msg.channel.id != 1286543172654207078:
        return
    async with msg.channel.typing():
        if msg.attachments: # 如果訊息中有檔案
            for attachment in msg.attachments: # 遍歷訊息中檔案
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']): # 檢測副檔名
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp: # 讀取圖片的 url 並將他用 aiohttp 函式庫轉換成數據
                            if resp.status != 200:
                                await msg.reply('圖片載入失敗。', mention_author=False) # 如果圖片分析失敗就不再執行下方程式
                                return
                            print(f'正在分析使用者的圖片...')
                         #   bot_msg = await msg.reply('正在分析圖片...', mention_author=False)
                            image_data = await resp.read() # 定義 image_data 為 aiohttp 回應的數據
                            response_text = await image_api(image_data, msg.content) # 用 image_api 函式來發送圖片數據跟文字給 api
                            print(f'使用者的圖片內容:{response_text}')
                            roles = [role.name for role in msg.author.roles if role != msg.guild.default_role]
                            history = await update_history(f"[{msg.author.display_name}(身分組:{', '.join(roles)})]: 傳送了一張圖片，內容是「{response_text}」")
                            response = await call_api(prompt + history)
                            await update_history("[model]: " + response)
                            await msg.reply(response.replace("[model]:",""))
                            print(response)
                            return

        global message_history
        if msg.content.lower() == "reset":
            message_history = []
            await msg.channel.send("對話紀錄已清除")
            return
        
        links = islink(msg.content)
        if links:
            word = ""
            for link in links:
                title = gettitle(link) # 取得連結中的 title
                word += msg.content.replace(link, f'(一個網址, 網址標題是: "{title}")\n' if title else '(一個網址, 網址無法辨識)\n')
            roles = [role.name for role in msg.author.roles if role != msg.guild.default_role]
            history = await update_history(f'[{msg.author.display_name}(身分組:{', '.join(roles)})]: {word}')
            print(word)
            response = await call_api(prompt + history)
            await update_history("[model]: " + response)
            await msg.reply(response.replace("[model]:",""))
            print(response)
            return

        roles = [role.name for role in msg.author.roles if role != msg.guild.default_role]
        history = await update_history(f"[{msg.author.display_name}(身分組:{', '.join(roles)})]: " + msg.content)
        print(":" + msg.content)
        response = await call_api(prompt + history)
        await update_history("[model]: " + response)
        await msg.reply(response.replace("[model]:",""))
        print(response)

#在本地執行
# ================
bot.run(bot_token)
# ================
