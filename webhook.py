from flask import Flask, request, jsonify
import os
from openai import OpenAI
import json
import re

app = Flask(__name__)

# 設置 OpenAI API 密鑰
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if client.api_key:
    print("✅ 成功抓到 OPENAI_API_KEY:", client.api_key[:5] + "...")
else:
    print("❌ 沒有找到 OPENAI_API_KEY")

# 載入 TYPE 和連結的對應關係
try:
    with open("links.json", "r", encoding="utf-8") as f:
        type_links = json.load(f)
except UnicodeDecodeError as e:
    print(f"讀取 links.json 時發生編碼錯誤：{e}")
    type_links = {}

# 載入配管試壓規範 JSON
try:
    with open("piping_specification.json", "r", encoding="utf-8") as f:
        piping_spec = json.load(f)
except FileNotFoundError:
    piping_specification = {}
    print("❌ 無法找到配管試壓規範的 JSON 檔案。")

def search_piping_spec(question):
    # 清理輸入問題，去除空格並轉換為小寫
    question_cleaned = re.sub(r"\s+", "", question).lower()
    
    # 定義關鍵字
    cleaning_keywords = ["化學清洗", "化學處理"]
    pressure_test_keywords = ["水壓測試", "氣壓測試" ]

    # 根據問題選擇關鍵字
    if "清洗" in question_cleaned or "去污" in question_cleaned:
        keywords = cleaning_keywords
    elif "測試" in question_cleaned or "壓力" in question_cleaned:
        keywords = pressure_test_keywords
    else:
        keywords = [question_cleaned]  # 使用問題本身作為關鍵字

    # 儲存匹配的章節與子章節
    matched_sections = []
    matched_titles = []
    total_matches = 0

    for chapter, data in piping_spec.items():
        title = data.get("title", "")
        content = data.get("content", {})
        
        chapter_matched = False

        # 優先比對章節標題
        if any(keyword in title.lower() for keyword in keywords):
            chapter_matched = True

        # 如果章節標題沒有命中，再檢查子章節
        if not chapter_matched:
            for sec_num, sec_text in content.items():
                sec_text_clean = re.sub(r"\s+", "", sec_text).lower()
                if question_cleaned in sec_text_clean:
                    chapter_matched = True
                    break

        # 如果有命中
        if chapter_matched:
            matched_sections.append(f"第{chapter}章 {title}")
            matched_titles.append(f"第{chapter}章 {title}")
            total_matches += 1

            sorted_content = sorted(content.items(), key=lambda x: x[0])
            for sec_num, sec_text in sorted_content:
                matched_sections.append(f"{sec_num} {sec_text}")
                matched_titles.append(f"第{chapter}章 {title} - {sec_num}")
                total_matches += 1

    if matched_sections:
        summary = "\n".join(matched_sections)
        # 不砍掉，回傳完整，讓上層決定要不要切分
        return summary, matched_titles, total_matches

    return "", [], 0

#LINE 按鈕程式
def payload_with_buttons(text, options):    
    return {
        "payload": {
            "line": {
                "type": "template",
                "altText": text,
                "template": {
                    "type": "buttons",
                    "text": text,
                    "actions": [
                        {"type": "message", "label": opt, "text": opt} for opt in options
                    ]
                }
            }
        }
    }

def query_download_link(category, source):
    links = {
        ("油漆", "塑化"): "https://tinyurl.com/yp59mpat",
        ("油漆", "企業"): "https://tinyurl.com/c73ajvpt\n保溫層下方油漆防蝕暫行辦法\nhttps://tinyurl.com/2s3me8jh",
        ("管支撐", "塑化"): "https://tinyurl.com/5vk67ywh",
        ("管支撐", "企業"): "https://tinyurl.com/msxhmnha",
        ("鋼構", "塑化"): "https://tinyurl.com/3tdcxe5v",
        ("鋼構", "企業"): "https://tinyurl.com/mvb9yzhw",
        ("保溫", "企業"): "https://tinyurl.com/2s4cb5cn"
    }
    return links.get((category, source), "查無對應的下載連結")
""" 
def extract_from_query(text):
    categories = ["管支撐", "油漆", "鋼構", "保溫"]
    sources = ["企業", "塑化"]

    category_keywords = {
        "管支撐": ["管支撐", "支撐", "管道支撐", "TYPE"],
        "油漆": ["油漆", "塗裝", "漆", "涂料", "painting"],
        "保溫": ["保溫", "隔熱", "熱保", "隔熱保溫"],
        "鋼構": ["鋼構", "鋼結構", "結構鋼", "鋼架", "結構", "結構體", "鋼板", "鋼鐵板", "鋼梁", "鋼樑", "鋼結構規範", "鋼構規範", "結構設計規範"],
    }

    actions_map = {
        "查詢": "詢問內容",
        "查": "詢問內容",
        "詢問": "詢問內容",
        "找": "詢問內容",
        "下載": "下載",
        "給我": "下載",
        "提供": "下載",
    }

    # 初始化返回結果
    extracted = {"category": "", "source": "", "action": ""}

    # 檢查是否有匹配的 category
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            extracted["category"] = category
            break

    # 檢查是否有匹配的 source，且保溫類別只會選擇企業
    if extracted["category"] == "保溫":
        extracted["source"] = "企業"
    else:
        for src in sources:
            if src in text:
                extracted["source"] = src
                break

    # 檢查是否有匹配的 action
    for keyword, mapped in actions_map.items():
        if keyword in text:
            extracted["action"] = mapped
            break

    return extracted """

def extract_from_query(text):
    # 初始化返回結果    
    extracted = {"category": "", "source": "", "action": ""}

    # 定義 category_keywords
    category_keywords = {
        "管支撐": ["管支撐", "支撐", "管道支撐", "TYPE"],
        "油漆": ["油漆", "塗裝", "漆", "涂料", "painting"],
        "保溫": ["保溫", "隔熱", "熱保", "隔熱保溫"],
        "鋼構": ["鋼構", "鋼結構", "結構鋼", "鋼架", "結構", "結構體", "鋼板", "鋼鐵板", "鋼梁", "鋼樑", "鋼結構規範", "鋼構規範", "結構設計規範"],
    }

    # 定義 sources
    sources = ["企業", "塑化"]

    # 定義 actions_map
    actions_map = {
        "查詢": "詢問內容",
        "查": "詢問內容",
        "詢問": "詢問內容",
        "找": "詢問內容",
        "下載": "下載",
        "給我": "下載",
        "提供": "下載",
    }

    # 檢查是否有匹配的 category
    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            extracted["category"] = category
            break

    # 檢查是否有匹配的 source，且保溫類別只會選擇企業
    if extracted["category"] == "保溫":
        extracted["source"] = "企業"
    else:
        for src in sources:
            if src in text:
                extracted["source"] = src
                break

    # 檢查是否有匹配的 action
    for keyword, action in actions_map.items():
        if keyword in text:
            extracted["action"] = action
            break

    return extracted


@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    query_result = req.get("queryResult", {})
    user_query = query_result.get("queryText", "")
    session = req.get("session", "")
    intent = query_result.get("intent", {}).get("displayName", "")

    # 讀取 context 中的參數
    context_params = {}
    for context in query_result.get("outputContexts", []):
        if "spec-context" in context.get("name", ""):
            context_params = context.get("parameters", {})

    def output_context(params):
        return [{
            "name": f"{session}/contexts/spec-context",
            "lifespanCount": 5,
            "parameters": params
        }] 


    # 統一取得參數：優先從 query 抽出，否則使用 context 中值
    extracted_data = extract_from_query(user_query)
    category = extracted_data.get("category", context_params.get("category", ""))
    source = extracted_data.get("source", context_params.get("source", ""))
    action = extracted_data.get("action", "")

    print(f"🧩 抽取結果: category={category}, source={source}, action={action}, intent={intent}")

    #if re.search(r"(?:TY(?:PE)?)[-\s]*\d{1,3}[A-Z]?", user_query.upper()):
        #category = "管支撐"
        #source = "塑化"
    
    # 檢查是否提到 TYPE 編號
    match = re.search(r"(?:TY(?:PE)?)[-\s]*0*(\d{1,3}[A-Z]?)", user_query.upper())
    if match:
        type_id = match.group(1)
        # 判斷是否有英文字尾
        if type_id[-1].isalpha():
            type_key = f"TYPE{type_id[:-1].zfill(2)}{type_id[-1]}"
        else:
            type_key = f"TYPE{type_id.zfill(2)}"

        if type_key in type_links:
            link = type_links[type_key]
            return jsonify({
                "fulfillmentText": f"這是管支撐規範（塑化）{type_key} 的下載連結：\n{link}"
            })
        else:
            return jsonify({
                "fulfillmentText": f"找不到 {type_key} 的對應連結，請確認是否輸入正確。"
            })
        
            # 如果提問者輸入的問題與之前的上下文無關，清空 source 和 action
    if not category and not source and not action:
        context_params = {}  # 清空上下文參數
        
    # ✅ 加入自動下載條件
    if (action == "下載" or user_query == "下載") and category and source:
        link = query_download_link(category, source)
        return jsonify({
            "fulfillmentText": f"這是 {category}（{source}）規範的下載連結：\n{link}",
            "outputContexts": output_context({"category": category, "source": ""})  # 清除 source
        })


    keywords = {"規範", "資料", "標準圖"}
    if any(k in user_query for k in keywords):
        if not category:
            return jsonify({
                "fulfillmentMessages": [payload_with_buttons("請選擇規範類別", ["管支撐", "油漆", "鋼構", "保溫"])],
                "outputContexts": [{
                    "name": f"{session}/contexts/spec-context",
                    "lifespanCount": 5,
                    "parameters": {}
                }]
            })
        elif not source:
            return jsonify({
                "fulfillmentMessages": [payload_with_buttons(f"{category}：請選擇來源類型", ["企業", "塑化"])],
                "outputContexts": [{
                    "name": f"{session}/contexts/spec-context",
                    "lifespanCount": 5,
                    "parameters": {"category": category}
                }]
            })
        else:
            return jsonify({
                "fulfillmentMessages": [
                    payload_with_buttons(
                        f"{category}（{user_query}）：請選擇下一步",
                        [f"下載{category}（{user_query}）", "詢問內容"]
                    )
                ],
                "outputContexts": [{
                    "name": f"{session}/contexts/spec-context",
                    "lifespanCount": 5,
                    "parameters": {"category": category, "source": source}
                }]
            })

    if user_query in ["企業", "塑化"] and category:
        return jsonify({
            "fulfillmentMessages": [
                payload_with_buttons(
                    f"{category}（{user_query}）：請選擇下一步",
                    [f"下載{category}（{user_query}）", "詢問內容"]
                )
            ],
            "outputContexts": [{
                "name": f"{session}/contexts/spec-context",
                "lifespanCount": 5,
                "parameters": {"category": category, "source": user_query}
            }]
        })    


    if user_query == "詢問內容":
        # 清除 source
        return jsonify({
            "fulfillmentText": "請問您想詢問哪段規範內容？例如：測試、清洗、壓力等。",
            "outputContexts": output_context({"category": category, "source": ""})  # 清除 source
        })

    if intent == "Default Fallback Intent":
        spec_summary, matched_titles, total_matches = search_piping_spec(user_query)

        if total_matches > 0:
            if len(spec_summary) > 500:
                reply = f"根據企業配管共同規範資料，找到相關內容(已截取)：\n{spec_summary[:500]}...\n🔔 內容過長，請查閱完整規範。"
            else:
                reply = f"根據企業配管共同規範資料，找到相關內容：\n{spec_summary}"
        else:
            # 如果找不到，呼叫ChatGPT
            try:
                print("🔍 呼叫 GPT-3.5-Turbo 回答...")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是配管設計專家，只回答與配管相關的問題。"},
                        {"role": "user", "content": user_query}
                    ],
                    max_tokens=500,
                    temperature=0.2,
                    top_p=0.8
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                print("❌ GPT 呼叫失敗:", e)
                reply = "抱歉，目前無法處理您的請求。請稍後再試。"

        return jsonify({
            "fulfillmentText": reply
        })
    # 如果不是 Default Fallback Intent，執行其他邏輯

    return jsonify({
        "fulfillmentMessages": [payload_with_buttons("請選擇規範類別3333", ["管支撐", "油漆", "鋼構", "保溫"])],
        "outputContexts": output_context({})
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# (Removed invalid Python code)ngrok http 5000