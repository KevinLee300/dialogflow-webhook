from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

# 設置 OpenAI API 密鑰
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json()
        query_result = req.get("queryResult", {})
        parameters = query_result.get("parameters", {})
        print("收到的參數：", parameters)
        output_contexts = query_result.get("outputContexts", [])
    except Exception as e:
        return jsonify({"fulfillmentText": "發生錯誤，請稍後再試。"})

    # 取得 Dialogflow 傳遞的參數
    spec_type = parameters.get("spec_type", "")  # 預設為空字串
    category = parameters.get("category", "")  # 新增 category 參數

    # 根據 spec_type 和 category 的值，產生不同的回覆
    if category == "管支撐":
        if spec_type == "塑化":
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
    else:
        # 使用 ChatGPT 生成回覆
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"根據以下參數生成回應：{parameters}",
                max_tokens=50
            )
            reply = response.choices[0].text.strip()
        except Exception as e:
            reply = "無法生成回應，請稍後再試。"

    # 回傳 JSON 格式的回應給 Dialogflow
    return jsonify({
        "fulfillmentText": reply,
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
