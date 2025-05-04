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
        piping_specification = json.load(f)
except FileNotFoundError:
    piping_specification = {}
    print("❌ 無法找到配管規範 JSON 檔案。")

try:
    with open("piping_heat_treatment.json", "r", encoding="utf-8") as f:
        piping_heat_treatment = json.load(f)
except FileNotFoundError:
    piping_heat_treatment = {}
    print("❌ 無法找到熱處理規範 JSON 檔案。")

#問題中文轉英文
def translate_to_english(query):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "請將下面的中文工程問題翻譯為簡潔精確的英文，供資料比對使用。"},
            {"role": "user", "content": query}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


""" def search_piping_spec(question, spec_data, keywords):
    question_cleaned = re.sub(r"\s+", "", question).lower()
    
    matched_sections = []
    matched_titles = []
    total_matches = 0

    for chapter, data in spec_data.items():
        title = data.get("title", "")
        content = data.get("content", {})

        chapter_matched = any(keyword in title.lower() for keyword in keywords)

        if not chapter_matched:
            for sec_num, sec_text in content.items():
                sec_text_clean = re.sub(r"\s+", "", sec_text).lower()
                if question_cleaned in sec_text_clean:
                    chapter_matched = True
                    break

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
        return summary, matched_titles, total_matches

    return "", [], 0 """

def search_piping_spec(question, spec_data, keywords):
    question_cleaned = re.sub(r"\s+", "", question).lower()
    
    matched_summaries = []
    matched_details = {}
    total_matches = 0

    for chapter, data in spec_data.items():
        title = data.get("title", "")
        content = data.get("content", {})

        for sec_num, sec_text in content.items():
            text_clean = re.sub(r"\s+", "", sec_text).lower()
            if any(kw in text_clean for kw in keywords) or question_cleaned in text_clean:
                key = f"第{chapter}章 {title} - {sec_num}"
                matched_summaries.append(key)
                matched_details[key] = sec_text
                total_matches += 1

    if matched_summaries:
        summary = "\n".join([f"{i+1}. {s}" for i, s in enumerate(matched_summaries)])
        return summary, matched_details, total_matches

    return "查無相關內容。", {}, 0


""" # def generate_spec_reply(user_query, spec_data, spec_type_desc):
#     keywords = {"規範", "資料", "標準圖", "查詢", "我要查", "查"}  # 定義關鍵字
#     summary, matched_titles, total_matches = search_piping_spec(user_query, spec_data, keywords)
#     if total_matches == 0:
#         english_query = translate_to_english(user_query)  # 翻譯成英文
#         summary, matched_titles, total_matches = search_piping_spec(english_query, spec_data, keywords)

#     if total_matches > 0:
#         if len(summary) > 500:
#             reply = f"根據《{spec_type_desc}》，找到相關內容（已截取）：\n{summary[:500]}...\n🔔 內容過長，請查閱完整規範。"
#         else:
#             reply = f"根據《{spec_type_desc}》，找到相關內容：\n{summary}"
#     else:
#         try:
#             print("🔍 呼叫 GPT 回答...")
#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[
#                     {"role": "system", "content": "你是配管設計專家，只回答與配管規範相關的問題。"},
#                     {"role": "user", "content": user_query}
#                 ],
#                 max_tokens=500,
#                 temperature=0.2,
#                 top_p=0.8
#             )
#             reply = response.choices[0].message.content.strip()
#         except Exception as e:
#             print("❌ GPT 呼叫失敗:", e)
#             reply = "抱歉，目前無法處理您的請求，請稍後再試。"

#     return jsonify({
#         "fulfillmentText": reply
#     })
 """




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
        ("保溫", "企業"): "https://tinyurl.com/2s4cb5cn",
        ("保溫", "塑化"): "保溫規範請參考企業規範\nhttps://tinyurl.com/2s4cb5cn"
    }
    return links.get((category, source), "查無對應的下載連結")

    # 定義 categories_map，類似 actions_map 的結構
category_keywords = {
        "管支撐": ["管支撐", "支撐", "管道支撐","PIPING SUPPORT","SUPPORT"],
        "油漆": ["油漆", "塗裝", "漆", "涂料", "painting"],
        "保溫": ["保溫", "隔熱", "熱保", "隔熱保溫"],
        "鋼構": ["鋼構", "鋼結構", "結構鋼", "鋼架", "結構", "結構體",
            "鋼板", "鋼鐵板", "鋼梁", "鋼樑", "鋼結構規範", "鋼構規範", "結構設計規範"],
    } 
action_keywords = {
    "詢問內容": ["查詢", "查", "詢問", "找"],
    "下載": ["下載", "給我", "提供"],}
sources = ["企業", "塑化"]
categories_map = {k: v for v, keys in category_keywords.items() for k in keys}
actions_map = {k: v for v, keys in action_keywords.items() for k in keys}


def extract_from_query(text):
    found = {"category": "", "source": "", "action": ""}

        # 檢查是否有匹配的 category
    for keyword, category in categories_map.items():
        if keyword in text:
            found["category"] = category
            break
    for s in sources:
        if s in text:
            found["source"] = s
            break
    if any(word in text for word in action_keywords["下載"]):
        found["action"] = "下載"
    elif any(word in text for word in action_keywords["詢問內容"]):
        found["action"] = "詢問內容"

    return found
       # 讀取 context 中的參數

@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    if not isinstance(req, dict):
        print(f"❌ 錯誤：req 不是字典，而是 {type(req)}")
        return jsonify({"fulfillmentText": "請求格式錯誤，請確保 Content-Type 為 application/json。"}) 

    query_result = req.get("queryResult", {})
    user_query = query_result.get("queryText", "")
    session = req.get("session", "")
    intent = req.get("queryResult", {}).get("intent", {}).get("displayName", "")

    # 讀取 context 中的參數
    context_params = {}
    for context in req.get("queryResult", {}).get("outputContexts", []):
        if "spec-context" in context.get("name", ""):
            context_params = context.get("parameters", {})

    def output_context(params):
        if not params or params.get("await_spec_selection") is False:
            # 清除上下文
            return [{
                "name": f"{session}/contexts/spec-context",
                "lifespanCount": 0,  # 設置 lifespanCount 為 0 清除上下文
                "parameters": {}
            }]
        else:
            # 保留上下文
            return [{
                "name": f"{session}/contexts/spec-context",
                "lifespanCount": 5,  # 設置上下文的有效期
                "parameters": params
            }]
   
    def generate_spec_reply(user_query, spec_data, spec_type_desc):
        keywords = {"規範", "資料", "標準圖", "查詢", "我要查", "查"}

        summary, matched_details, total_matches = search_piping_spec(user_query, spec_data, keywords)

        if total_matches == 0:
            english_query = translate_to_english(user_query)
            summary, matched_details, total_matches = search_piping_spec(english_query, spec_data, keywords)

        if total_matches > 0:
            reply = f"根據《{spec_type_desc}》，找到 {total_matches} 筆相關內容：\n{summary}\n請輸入對應的項目編號查看詳細內容（例如輸入 1）"
            
            # 回傳 matched_details（可序列化）存在 context 中
            return jsonify({
                "fulfillmentText": reply,
                "outputContexts": output_context({
                    "await_spec_selection": True,
                    "spec_options": list(matched_details.items())  # 傳成 list 才能序列化成 JSON
                })
            })
        else:
            # 🔁 fallback to GPT
            try:
                print("🔍 呼叫 GPT 回答...")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是配管設計專家，只回答與配管規範相關的問題。"},
                        {"role": "user", "content": user_query}
                    ],
                    max_tokens=500,
                    temperature=0.2,
                    top_p=0.8
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                print("❌ GPT 呼叫失敗:", e)
                reply = "抱歉，目前無法處理您的請求，請稍後再試。"

            return jsonify({
                "fulfillmentText": reply
            })
    
    if context_params.get("await_spec_selection"):
        user_choice = user_query.strip()
        spec_items = context_params.get("spec_options", [])

        if not spec_items:
            # 如果上下文中沒有選項，清除上下文並退出
            return jsonify({
                "fulfillmentText": "上下文已過期，請重新查詢。",
                "outputContexts": output_context({})
            })

        print(f"🔍 Debug: user_choice={user_choice}, spec_items={spec_items}")

        if user_choice.isdigit():
            index = int(user_choice) - 1
            if 0 <= index < len(spec_items):
                title, content = spec_items[index]

                # 清除上下文
                return jsonify({
                    "fulfillmentText": f"📘 您選擇的是：{title}\n內容如下：\n{content}",
                    "outputContexts": output_context({})  # 清除上下文
                })
            else:
                return jsonify({
                    "fulfillmentText": f"請輸入有效的數字（例如 1~{len(spec_items)}）"
                })
        else:
            return jsonify({
                "fulfillmentText": "請輸入項目編號（例如 1 或 2），以查看詳細內容。"
            })
    if intent == "User Selects Spec Item":
        user_choice = user_query.strip()
        spec_items = context_params.get("spec_options", [])

        if not spec_items:
            return jsonify({
                "fulfillmentText": "目前沒有可供選擇的項目，請先提出查詢。"
            })

        if user_choice.isdigit():
            index = int(user_choice) - 1
            if 0 <= index < len(spec_items):
                title, content = spec_items[index]
                return jsonify({
                    "fulfillmentText": f"📘 您選擇的是：{title}\n內容如下：\n{content}",
                    "outputContexts": output_context({})  # ✅ 清除 context
                })
            else:
                return jsonify({
                    "fulfillmentText": f"請輸入有效的數字（例如 1~{len(spec_items)}）"
                })
        else:
            return jsonify({
                "fulfillmentText": "請輸入有效的項目編號，例如 1 或 2。"
            })        
    elif intent == "詢問熱處理規範":
        print(f"🔍 Debug熱處理: intent={intent}, user_query={user_query}, context_params={context_params}")
        spec_reply = generate_spec_reply(user_query, piping_heat_treatment, "詢問熱處理規範")
        return jsonify({
            "fulfillmentText": spec_reply.get_json()["fulfillmentText"],
            "outputContexts": output_context({
                "await_heat_question": True,
                "await_spec_selection": True
            })
        })
    elif intent == "查詢規範2":
        # 統一取得參數：優先從 query 抽出，否則使用 context 中值
        extracted_data = extract_from_query(user_query)
        category = extracted_data.get("category", context_params.get("category", ""))
        source = extracted_data.get("source", context_params.get("source", ""))
        action = extracted_data.get("action", context_params.get("action", ""))

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
            
        print(f"🧩 抽取結果: category={category}, source={source}, action={action}, intent={intent}")  
        
        # ✅ 加入自動下載條件
        if action == "下載" and category and source:
            link = query_download_link(category, source)
            return jsonify({
                "fulfillmentText": f"這是 {category}（{source}）規範的下載連結：\n{link}",
                "outputContexts": output_context({"category": category, "source": ""})  # 清除 source
            })

        keywords = {"規範", "資料", "標準圖", "查詢", "我要查", "查"}
        if any(k in user_query for k in keywords):
            if not category:
                print(f"🔍 Debug: category={category}, source={source}, action={action}")
                return jsonify({
                    "fulfillmentMessages": [payload_with_buttons("請選擇規範類別", ["查管支撐", "查油漆", "查鋼構", "查保溫"])],
                    "outputContexts": [{
                        "name": f"{session}/contexts/spec-context",
                        "lifespanCount": 5,
                        "parameters": {"source": source, "action": action}
                    }]
                })
            elif not source:
                return jsonify({
                    "fulfillmentMessages": [payload_with_buttons(f"{category}：請選擇來源類型", ["企業", "塑化"])],
                    "outputContexts": [{
                        "name": f"{session}/contexts/spec-context",
                        "lifespanCount": 5,
                        "parameters": {"category": category, "action": action}
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
        if user_query in ["企業", "塑化"]:
            # 從上下文中提取 category 和 action
            remembered_category = context_params.get("category", "")
            remembered_action = context_params.get("action", "")
            
            print(f"🔍 Debug: remembered_category={remembered_category}, remembered_action={remembered_action}, user_query={user_query}")
            
            if remembered_category:
                if remembered_action == "下載":
                    link = query_download_link(remembered_category, user_query)
                    return jsonify({
                        "fulfillmentText": f"這是 {remembered_category}（{user_query}）規範的下載連結：\n{link}",
                        "outputContexts": [{
                            "name": f"{session}/contexts/spec-context",
                            "lifespanCount": 5,
                            "parameters": {
                                "category": remembered_category,
                                "source": user_query,
                                "action": remembered_action
                            }
                        }]
                    })
                else:
                    return jsonify({
                        "fulfillmentMessages": [
                            payload_with_buttons(
                                f"{remembered_category}（{user_query}）：請選擇下一步",
                                [f"下載{remembered_category}（{user_query}）", "詢問內容"]
                            )
                        ],
                        "outputContexts": [{
                            "name": f"{session}/contexts/spec-context",
                            "lifespanCount": 5,
                            "parameters": {
                                "category": remembered_category,
                                "source": user_query,
                                "action": remembered_action
                            }
                        }]
                    })
            else:
                return jsonify({
                    "fulfillmentMessages": [payload_with_buttons("請選擇規範類別", ["管支撐", "油漆", "鋼構", "保溫"])],
                    "outputContexts": output_context({"source": user_query, "action": remembered_action})
                })


        if user_query == "詢問內容":
            # 清除 source
                return jsonify({
                    "fulfillmentText": "請問您想詢問哪段規範內容？例如：測試、清洗、壓力等。",
                    "outputContexts": output_context({"category": category, "source": ""})  # 清除 source
                })  
        
        return jsonify({
        "fulfillmentMessages": [payload_with_buttons("請選擇規範類別3333", ["查詢管支撐", "查詢油漆", "查詢鋼構", "查詢保溫"])],
        "outputContexts": output_context({})
    })

    elif intent == "詢問管線等級問題回答":
        try:
            print("💬 由 GPT 回答規範內容...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # 建議使用 gpt-4 或 gpt-4-turbo
                messages=[
                    {"role": "system", "content": "你是配管設計專家，只回答與工程規範、標準圖或施工標準相關的問題，請根據使用者的問題提供清楚簡潔的回答。"},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=500,
                temperature=0.2,
                top_p=0.8
            )
            reply = response.choices[0].message.content.strip()
            return jsonify({
            "fulfillmentText": reply,
            "outputContexts": output_context({"await_pipeclass_question": True})
        })
        except Exception as e:
            print("❌ GPT 呼叫失敗:", e)
            reply = "抱歉，目前無法處理您的請求，請稍後再試。"

        return jsonify({
            "fulfillmentText": reply,
            "outputContexts": output_context({"await_pipeclass_question": True})
        })     
    


    elif intent == "Default Fallback Intent":
        if context_params.get("await_spec_selection") :#and user_query.strip().isdigit():
            print(f"🔍 Debug: user_choice={user_choice}, spec_items={spec_items}")
            # ✅ 模擬觸發 User Selects Spec Item intent
            user_choice = user_query.strip()
            spec_items = context_params.get("spec_options", [])
            index = int(user_choice) - 1
            if 0 <= index < len(spec_items):
                title, content = spec_items[index]
                return jsonify({
                    "fulfillmentText": f"📘 您選擇的是：{title}\n內容如下：\n{content}",
                    "outputContexts": output_context({})
                })
            else:
                return jsonify({
                    "fulfillmentText": f"請輸入有效的數字（例如 1~{len(spec_items)}）",
                    "outputContexts": output_context({"await_spec_selection": True})
                })
       # 🔁 處理熱處理後續問題
        elif context_params.get("await_heat_question"):
            print("🔄 重新路由到熱處理規範")
            return generate_spec_reply(user_query, piping_heat_treatment, "詢問熱處理規範")

        # 🔁 處理其他規範問題
        elif context_params.get("await_pipeclass_question"):
            try:
                print("💬 由 GPT 回答規範內容...")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是配管設計專家，只回答與工程規範、標準圖或施工標準相關的問題。"},
                        {"role": "user", "content": user_query}
                    ],
                    max_tokens=500,
                    temperature=0.2,
                    top_p=0.8
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                print("❌ GPT 呼叫失敗:", e)
                reply = "抱歉，目前無法處理您的請求，請稍後再試。"

            return jsonify({
                "fulfillmentText": reply
            })   
 
    else: 
        return generate_spec_reply(user_query, piping_specification, "企業配管共同規範")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# (Removed invalid Python code)ngrok http 5000