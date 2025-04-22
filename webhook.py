from flask import Flask, request, jsonify
import os

app = Flask(__name__)

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
        reply = "請問是要查詢「塑化」還是「企業」規範？"  # 詢問規範類型

    # 回傳 JSON 格式的回應給 Dialogflow
    return jsonify({
        "fulfillmentText": reply
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)