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

        # [최종 수정된 스타일 가이드 적용 프롬프트]
        system_instruction = (
            "당신은 문체 변환기입니다. 주어진 문장의 의미는 그대로 유지하되, 아래 [스타일 가이드]에 맞춰 말투만 바꾸십시오.\n\n"
            "### [스타일 가이드] ###\n"
            f"{persona['system']}\n\n"
            "### [절대 규칙] ###\n"
            "1. 문장의 주어와 내용은 변경하지 마십시오.\n"
            "2. 대화하거나 질문에 답하지 마십시오.\n"
            "3. 입력된 문장을 위 스타일로 '다시 쓰기'만 하십시오.\n"
            "4. 사족 없이 변환된 문장 하나만 출력하십시오."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"입력 문장: [{text}]\n변환 결과:"}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.7, # 창의성을 위해 온도 약간 상승
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
