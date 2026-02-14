import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

# 절대 경로 설정
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

        # 비즈니스 변환을 위한 엄격한 시스템 지침
        system_instruction = (
            f"{persona['system']}\n\n"
            "### [작업 규칙] ###\n"
            "1. 입력된 내용을 바탕으로 비즈니스 상황에 적합한 문장으로 완전히 재작성하십시오.\n"
            "2. 절대로 사용자의 말에 대답하거나 사견을 덧붙이지 마십시오.\n"
            "3. 변환된 결과물 외에 어떠한 부연 설명이나 따옴표도 출력하지 마십시오."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": persona['user_template'].format(text=text)}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.3, # 비즈니스 어투의 일관성을 위해 낮은 온도 유지
            max_tokens=500
        )

        transformed_text = chat_completion.choices[0].message.content.strip()
        transformed_text = transformed_text.replace("\"", "").strip()

        return jsonify({
            "persona_id": persona_id,
            "original_text": text,
            "transformed_text": transformed_text
        }), 200

    except Exception as e:
        return jsonify({"error": f"서버 통신 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
