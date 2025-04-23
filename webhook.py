from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

# 設置 OpenAI API 密鑰
openai.api_key = 'sk-proj-wvFR6OgGFWPq_DNC5dXYhsk-uWSk2I9e5kRH8LL4P97wjYdyzs6agpybJClc5eblJpIDbruZaeT3BlbkFJbixS6m5q2Z7IrdHb7gtnehiyn2TGbyN4vGyh3L2VoSbMicjPcVIvtoFs56Qes_rlRS4ZkkX8gAY'

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()

    # 取得 Dialogflow 傳遞的參數
    query_result = req.get("queryResult", {})
    parameters = query_result.get("parameters", {})
    spec_type = parameters.get("spec_type", "")  # 預設為空字串

    # 根據 spec_type 的值，產生不同的回覆
    if spec_type == "塑化":
        reply = "這是塑化規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/ERTtlkWS33tJjZ4yg2-COYkBVv1DBbVmg0ui8plAduBb4A?e=AE5ybU"
    elif spec_type == "企業":
        reply = "這是企業規範的下載連結：\nhttps://1drv.ms/b/c/c2f6a4a69f694f7a/ERaG7Grpi7RLhLySygar-E0BqPzegJZTQK19aBUs01C55g?e=Bk6Cgz"
    else:
        # 使用 ChatGPT 生成回覆
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt="請問是要查詢「塑化」還是「企業」規範？",
            max_tokens=50
        )
        reply = response.choices[0].text.strip()

    # 回傳 JSON 格式的回應給 Dialogflow
    return jsonify({
        "fulfillmentText": reply
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)