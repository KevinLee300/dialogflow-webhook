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
        ("油漆", "企業"): "https://tinyurl.com/c73ajvpt",
        ("管支撐", "塑化"): "https://tinyurl.com/5vk67ywh",
        ("管支撐", "企業"): "https://tinyurl.com/msxhmnha"
    }
    return links.get((category, source), "查無對應的下載連結")

def extract_from_query(text):
    categories = ["管支撐", "油漆"]
    sources = ["企業", "塑化"]
    actions_map = {
        "查詢": "詢問內容",
        "查": "詢問內容",
        "詢問": "詢問內容",
        "找": "詢問內容",
        "下載": "下載",
        "給我": "下載",
        "提供": "下載",
    }

    found = {}
    for c in categories:
        if c in text:
            found["category"] = c
    for s in sources:
        if s in text:
            found["source"] = s
    for keyword, action in actions_map.items():
        if keyword in text:
            found["action"] = action
            break
    return found


@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    query_result = req.get("queryResult", {})
    user_query = query_result.get("queryText", "")
    session = req.get("session", "")
    intent = query_result.get("intent", {}).get("displayName", "")

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
    extracted = extract_from_query(user_query)
    category = extracted.get("category", context_params.get("category", ""))
    source = extracted.get("source", context_params.get("source", ""))
    action = extracted.get("action", "")



    # 主邏輯處理
    if action or any(keyword in user_query for keyword in ["規範", "資料", "標準圖"]):
        if not category: # 如果沒有指定 category，讓用戶選擇規範類別
            return jsonify({
                "fulfillmentMessages": [payload_with_buttons("請選擇規範類別", ["管支撐", "油漆"])],
                "outputContexts": output_context({})
            })
        elif not source: # 如果已經指定了 category，則提示選擇來源類型
            return jsonify({
                "fulfillmentMessages": [payload_with_buttons(f"{category}：請選擇來源類型", ["企業", "塑化"])],
                "outputContexts": output_context({"category": category})
            })
        elif action == "下載":
            link = query_download_link(category, source)
            return jsonify({
                "fulfillmentText": f"這是 {category}（{source}）規範的下載連結：\n{link}"
            })
        else:
            return jsonify({
                "fulfillmentMessages": [payload_with_buttons(f"{category}（{source}）：請選擇下一步", ["下載", "詢問內容"])],
                "outputContexts": output_context({"category": category, "source": source})
            })

    if user_query in ["企業", "塑化"] and category:
        return jsonify({
            "fulfillmentMessages": [payload_with_buttons(f"{category}（{user_query}）：請選擇下一步", ["下載", "詢問內容"])],
            "outputContexts": output_context({"category": category, "source": user_query})
        })


    if user_query == "下載" and category and source:
        link = query_download_link(category, source)
        return jsonify({"fulfillmentText": f"這是 {category}（{source}）規範的下載連結：\n{link}"})

    if user_query == "詢問內容":
        return jsonify({"fulfillmentText": "請問您想詢問哪段規範內容？例如：測試、清洗、壓力等。"})

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

    return jsonify({"fulfillmentText": "請輸入有效的查詢，例如：查詢規範、管支撐、油漆等。"})

    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# (Removed invalid Python code)ngrok http 5000