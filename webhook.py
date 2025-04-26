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
    # 移除不必要的空白字符並轉小寫
    question_cleaned = question.replace("\u3000", " ").replace(" ", "").lower()
    
    # 定義關鍵字列表（這些關鍵字可能與化學清洗相關）
    keywords = ["化學清洗", "清洗要求", "清潔", "去污", "化學處理"]
    keywords = ["水壓測試", "耐壓測試", "爆破壓力", "水面下測試", "壓力測試", "耐壓", "氣密測試"]

    # 儲存匹配的內容
    matched_sections = []
    matched_titles = []  # 儲存匹配段落的標題
    total_matches = 0  # 總匹配數量
    
    # 檢查問題中是否有關鍵字，並匹配相關段落
    for chapter, data in piping_spec.items():
        title = data.get("title", "")
        content = data.get("content", {})
        
        for sec_num, sec_text in content.items():
            # 清理段落文字，移除空白字符並轉小寫
            sec_text_clean = sec_text.replace("\u3000", " ").replace(" ", "").lower()
            
            # 檢查問題中的任何關鍵字是否出現在該段落中
            if any(keyword in sec_text_clean for keyword in keywords):
                matched_sections.append(sec_text)
                matched_titles.append(f"第{chapter}章 {title} - {sec_num}")
                total_matches += 1
    if matched_sections:
        # 取出前三個匹配的段落，並進行簡短摘要
        summary = "\n\n".join(matched_sections[:3])  # 只取前三個匹配的段落
        summary = summary[:400]  # 確保回覆不超過1000字符
        return summary, matched_titles, total_matches
    # 返回找到的匹配段落（最多三個），還有標題和總匹配數量
    return "未找到相關水壓測試的規範，請確認問題關鍵字。", [], 0


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json()
        query_result = req.get("queryResult", {})
        parameters = query_result.get("parameters", {})
        for context in query_result.get("outputContexts", []):
            if context.get("name", "").endswith("/contexts/query-followup"):
                context_params = context.get("parameters", {})
                parameters.setdefault("category", context_params.get("category", ""))
                parameters.setdefault("spec_type", context_params.get("spec_type", ""))
                parameters.setdefault("TYPE", context_params.get("type", ""))

        session = req.get("session", "")
        intent = query_result.get("intent", {}).get("displayName", "")
        user_query = query_result.get("queryText", "")  # 提取使用者的原始輸入
    except Exception as e:
        return jsonify({"fulfillmentText": "發生錯誤，請稍後再試。"})

    # 如果是 Default Fallback Intent
    if intent == "Default Fallback Intent":
        spec_summary, matched_titles, total_matches = search_piping_spec(user_query)
        if spec_summary:
            reply = f"根據配管規範資料，找到相關內容：\n{spec_summary}"
            if total_matches > 3:
                reply += "\n🔔 尚有更多相關章節，建議詳閱完整規範。"
        else:
            # 找不到，才用 ChatGPT 回答
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是配管設計專家，不回答與配管無關的訊息。"},
                        {"role": "user", "content": "請簡短回答：" + user_query}
                    ],
                    max_tokens=150,
                    temperature=0.2,
                    top_p=0.8
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                reply = "抱歉，我無法處理您的請求，請稍後再試。"

        return jsonify({
            "fulfillmentText": reply
        })
    # 如果不是 Default Fallback Intent，執行其他邏輯
    category = parameters.get("category", "")
    spec_type = parameters.get("spec_type", "")
    type_key = parameters.get("TYPE", "").upper()

    if category == "油漆":
        if spec_type == "塑化":
            reply = "這是油漆塑化規範的下載連結：\nhttps://tinyurl.com/yp59mpat"
        elif spec_type == "企業":
            reply = "這是油漆企業規範的下載連結：\nhttps://tinyurl.com/c73ajvpt"
        else:
            reply = "請問是要查詢油漆的「塑化」還是「企業」規範？"
    elif category == "管支撐":
        if spec_type == "塑化":
            reply = "這是管支撐塑化規範的下載連結：\nhttps://tinyurl.com/5vk67ywh"
        elif spec_type == "企業":
            reply = "這是管支撐企業規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/ERaG7Grpi7RLhLySygar-E0BqPzegJZTQK19aBUs01C55g?e=c9cAOS"
        elif "TYPE" in type_key.upper():
            if type_key.upper() in type_links:
                reply = f"這是管支撐 {type_key} 的下載連結：\n{type_links[type_key.upper()]}"
            else:
                reply = "請提供有效的 TYPE（例如 TYPE01 ~ TYPE140）。"
        else:
            reply = "請問是要查詢管支撐的「塑化」還是「企業」規範？"   
    else:
        reply = "請提供有效的類別（例如 管支撐 或 油漆）。"

    return jsonify({
        "fulfillmentText": reply,
        "outputContexts": [
            {
                "name": f"{session}/contexts/query-followup",
                "lifespanCount": 5,
                "parameters": {
                    "category": category,
                    "spec_type": spec_type,
                    "type": type_key
                }
            }
        ]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
