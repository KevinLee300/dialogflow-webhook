from flask import Flask, request, jsonify
import os
from openai import OpenAI
import json
import logging

app = Flask(__name__)

# 設置 OpenAI API 密鑰
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if client.api_key:
    print("✅ 成功抓到 OPENAI_API_KEY:", client.api_key[:5] + "...")
else:
    print("❌ 沒有找到 OPENAI_API_KEY")

# 配置日誌
#logging.basicConfig(level=logging.INFO)

# 載入 TYPE 和連結的對應關係
try:
    with open("links.json", "r", encoding="utf-8") as f:
        type_links = json.load(f)
except UnicodeDecodeError as e:
    print(f"讀取 links.json 時發生編碼錯誤：{e}")
    type_links = {}

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

    # 如果是 Default Fallback Intent，直接呼叫 OpenAI API
    if intent == "Default Fallback Intent":
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位擅長配管設計的專家，只用最簡短直接的方式回答問題，請避免多餘解釋。"
                    },
                    {"role": "user", "content": "請簡短回答：" + user_query}
                ],
                max_tokens=150,
                temperature=0.2,
                top_p=0.8
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = "抱歉，我無法處理您的請求，請稍後再試。"

        # 直接返回 OpenAI 的回應
        return jsonify({
            "fulfillmentText": reply
        })

    # 如果不是 Default Fallback Intent，執行其他邏輯
    category = parameters.get("category", "")
    spec_type = parameters.get("spec_type", "")
    type_key = parameters.get("TYPE", "").upper()

    if category == "油漆":
        if spec_type == "塑化":
            reply = "這是油漆塑化規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/EVuPjaS3PC9JkmZFXK9Oh_MBk4zHIYJFQNs2mYOgzqILaQ?e=zDIdfA"
        elif spec_type == "企業":
            reply = "這是油漆企業規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/Eebe8nZcWq9EjuakO8mqU9EBzk53IDJ24jtspI6VDlb5Tg?e=1E9yWu"
        else:
            reply = "請問是要查詢油漆的「塑化」還是「企業」規範？"
    elif category == "管支撐":
        if spec_type == "塑化":
            reply = "這是管支撐塑化規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/ERTtlkWS33tJjZ4yg2-COYkBVv1DBbVmg0ui8plAduBb4A?e=edJfNW"
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
