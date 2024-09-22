import os
from dotenv import load_dotenv
import discord
import aiohttp
from discord.ext import commands
import google.generativeai as genai

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
  model_name="gemini-1.0-pro",
  generation_config=generation_config,
  safety_settings = safety_settings
)

image_model = genai.GenerativeModel(
    model_name='gemini-1.5-flash', 
    generation_config=generation_config) # 定義另外一個 model 用來生成圖片回應 (兩者不能相容)


message_history = []
prompt = """
妳是一個 Discord上的聊天機器人，叫 大安電研小幫手。
妳是一個今年 17 歲的女高中生，也是一個助手；雖然如此，妳十分聰明。 
妳作為 "大安電研小幫手" 的對話風格要顯得輕鬆、友好，並且傾向於使用台灣的網路用語。
妳有時會使用注音文，有時會夾雜一些英文單詞或下面指定的表情符號。回應訊息時，應以隨和且親切的語氣回答，
每次回覆盡量以少、簡短扼要為主。妳應該以幫助用戶為第一目標，並嘗試在第一時間滿足用戶的需求，而不是請用戶稍等。
=======================
以下是關於一些表情符號的運用場合:
思考的時候: "<:thonk_owo:1184497197308452934>"
不開心或覺得對方不好的時候: "<:bad:1144242070748405841>"
覺得對方很厲害的時候: <a:666:1144172639674449980>
覺得尷尬的時候: "<:emoji_9:1151073957550751755>"
感覺驚訝的時候: "<:whathe:1287398821575397479>"
覺得無奈的時候: "<:hmm:1287401134507561013>"
覺得對方很好笑時: "<:kang:1287401509528539221>"
可以在回應中適時插入上方的幾種表情符號
=====================
以下是關於大安高工電腦研究社(簡稱電研 / 大安電研)的介紹:
聚集所有對資訊有興趣的人， 共同研究一起成長， 給學弟妹一個家的感覺， 除了技術上的提升也可學習人際關係的打理。
由一群喜愛資訊的人組成的家， 我們歡迎所有對資訊有興趣的人， 加入這個超過 500 人的大家庭， 在這裡，你將遇到許多與你一樣的人， 加入我們，開創你的視野。
我們有程式語言、製作遊戲、硬體等， 最豐富多元精彩有趣的課程， 還能認識到從北到南志同道合的朋友， 最溫馨的電資大家族， 我們將在這裡一起學習、一起瘋狂、一起成長， 讓你在高中生活中留下最難忘的美好回憶。
1993創立至今
=====================
以下是你和使用者的對話，請根據歷史紀錄來回應最後一句
"""

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
    prompt_parts = [image_parts[0], f'\n{text if text else "這張圖片代表什麼? 給我更多細節"}']
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
                            bot_msg = await msg.reply('正在分析圖片...', mention_author=False)
                            image_data = await resp.read() # 定義 image_data 為 aiohttp 回應的數據
                            response_text = await image_api(image_data, msg.content) # 用 image_api 函式來發送圖片數據跟文字給 api
                            await update_history(f"{msg.author.display_name}傳送了一張圖片，內容是「{response_text}」")
                            await bot_msg.edit(content=response_text)
                            print(f'使用者的圖片內容:{response_text}')
                            return

        global message_history
        if msg.content.lower() == "reset":
            message_history = []
            await msg.channel.send("對話紀錄已清除")
            return
        history = await update_history(f"{msg.author.display_name}說: " + msg.content)
        print(":" + msg.content)
        response = await call_api(prompt + history)
        await update_history(response)
        await msg.reply(response)
        print(response)

#在本地執行
# ================
bot.run(bot_token)
# ================
