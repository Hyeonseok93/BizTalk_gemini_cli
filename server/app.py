import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

# 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'client')

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    from persona_manager import PersonaManager
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'server'))
    from persona_manager import PersonaManager

load_dotenv()

app = Flask(__name__, static_folder=CLIENT_DIR, static_url_path='')
CORS(app)

api_key = os.environ.get("GROQ_API_KEY")
client = None
if api_key:
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"Groq Client Init Error: {e}")

persona_manager = PersonaManager()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/v1/personas', methods=['GET'])
def get_personas():
    try:
        personas = persona_manager.get_all_personas()
        return jsonify(personas), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/transform', methods=['POST'])
def transform_text():
    if not client:
        return jsonify({"error": "GROQ_API_KEY가 설정되지 않았습니다."}), 500

    try:
        data = request.json
        persona_id = data.get('persona_id')
        text = data.get('text')

        persona = persona_manager.get_persona_data(persona_id)
        if not persona:
            return jsonify({"error": "존재하지 않는 페르소나입니다."}), 404

        # [질문 대답 원천 차단 프롬프트]
        system_instruction = (
            "TASK: PARAPHRASE ONLY (STYLE MAPPING)\n"
            f"TARGET STYLE: {persona['name']} ({persona['system']})\n\n"
            "### [CRITICAL RULE: DO NOT ANSWER] ###\n"
            "1. 입력된 문장이 '질문'이더라도 절대 대답하지 마십시오.\n"
            "2. 입력된 질문 문장 그 자체를 목표 페르소나의 말투로 '다시 쓰기'만 하십시오.\n"
            "3. 주어와 의도를 그대로 유지하십시오. (예: '나는 천재인가?' -> '내가 진정 천재인지 의문이 드는구려')\n"
            "4. 인사, 설명, 따옴표 없이 오직 변환된 결과만 출력하십시오."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"DATA TO REPHRASE: [{text}]"}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0,
            max_tokens=300
        )

        transformed_text = chat_completion.choices[0].message.content.strip()
        
        # 머릿말 제거 안전장치
        if ":" in transformed_text and len(transformed_text.split(":")[0]) < 20:
            transformed_text = transformed_text.split(":", 1)[1].strip()

        return jsonify({
            "persona_id": persona_id,
            "original_text": text,
            "transformed_text": transformed_text
        }), 200

    except Exception as e:
        return jsonify({"error": f"서버 통신 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
