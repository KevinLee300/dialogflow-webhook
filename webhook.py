from flask import Flask, request, jsonify
import os
import openai
import json
import logging

app = Flask(__name__)

# 設置 OpenAI API 密鑰
openai.api_key = os.getenv("OPENAI_API_KEY")

if openai.api_key:
    print("✅ 成功抓到 OPENAI_API_KEY:", openai.api_key[:5] + "...")
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
        #logging.info("收到的參數：%s", parameters)

    except Exception as e:
        return jsonify({"fulfillmentText": "發生錯誤，請稍後再試。"})
    session = req.get("session", "") 
    category = parameters.get("category", "")
    spec_type = parameters.get("spec_type", "")
    type_key = parameters.get("TYPE", "").upper()  # 假設 Dialogflow 傳遞的 TYPE 參數名稱為 "type"
    
    intent = query_result.get("intent", {}).get("displayName", "")
        
    if intent == "Default Fallback Intent":
            # 當為 Fallback Intent 時，發送請求給 OpenAI 生成回應
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # 或 "gpt-4"，根據你的需求選擇模型
                messages=[
                    {"role": "system", "content": "你是一個有幫助的助手。"},
                    {"role": "user", "content": f"根據以下參數生成回應：{parameters}"}
                ],
                max_tokens=50
            )
            reply = response["choices"][0]["message"]["content"].strip()
    else:
            reply = "請提供更多信息，我會幫助您。"

    if not category:
        contexts = req.get("queryResult", {}).get("outputContexts", [])
        for ctx in contexts:
            params = ctx.get("parameters", {})
            if "category" in params:
                category = params["category"]
                break


    if category == "管支撐":
        # 檢查是否有 TYPE 的請求
        if "TYPE" in type_key.upper():  # 將 type_key 轉為大寫進行檢查
            if type_key.upper() in type_links:  # 同樣將 type_key 轉為大寫匹配 type_links
                reply = f"這是管支撐 {type_key} 的下載連結：\n{type_links[type_key.upper()]}"
            else:
                reply = "請提供有效的 TYPE（例如 TYPE01 ~ TYPE140）。"
        # 處理 spec_type 的邏輯
        elif spec_type == "塑化":
            reply = "這是管支撐塑化規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/ERTtlkWS33tJjZ4yg2-COYkBVv1DBbVmg0ui8plAduBb4A?e=edJfNW"
        elif spec_type == "企業":
            reply = "這是管支撐企業規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/ERaG7Grpi7RLhLySygar-E0BqPzegJZTQK19aBUs01C55g?e=c9cAOS"
        else:
            reply = "請問是要查詢管支撐的「塑化」還是「企業」規範？"
    elif category == "油漆":
        if spec_type == "塑化":
            reply = "這是油漆塑化規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/EVuPjaS3PC9JkmZFXK9Oh_MBk4zHIYJFQNs2mYOgzqILaQ?e=zDIdfA"
        elif spec_type == "企業":
            reply = "這是油漆企業規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/Eebe8nZcWq9EjuakO8mqU9EBzk53IDJ24jtspI6VDlb5Tg?e=1E9yWu"
        else:
            reply = "請問是要查詢油漆的「塑化」還是「企業」規範？"


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
