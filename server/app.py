import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

# 현재 파일의 절대 경로를 기준으로 설정
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

# 로컬 테스트를 위해 절대 경로로 프론트엔드 폴더 지정
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

        # 시스템 지침에서 혼란을 줄 수 있는 중괄호 예시 제거
        system_instruction = (
            f"당신은 {persona['name']}의 말투로 문장을 재구성하는 변환 엔진입니다.\n\n"
            "### [필수 규칙] ###\n"
            f"1. 지침: {persona['system']}\n"
            "2. 화자 유지: 입력된 문장의 주어(나, 우리 등)가 말하는 의도와 정보를 그대로 유지하십시오.\n"
            "3. 대화 금지: 사용자의 말에 대답하거나 의견을 달지 마십시오. 질문도 하지 마십시오.\n"
            "4. 무설명 원칙: '변환된 문장입니다'와 같은 설명이나 제목, 따옴표 없이 오직 결과만 출력하십시오."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": "나는 배가 고프다."},
                {"role": "assistant", "content": "뱃속에서 요란한 소리가 들리니, 무언가 요기할 것을 찾아야겠구려."},
                {"role": "user", "content": text}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0,  # 가장 일관성 있는 결과
            max_tokens=300
        )

        transformed_text = chat_completion.choices[0].message.content.strip()
        # 불필요한 따옴표나 머리말 제거 강제 로직
        transformed_text = transformed_text.split('\n')[-1].replace("\"", "").strip()

        return jsonify({
            "persona_id": persona_id,
            "original_text": text,
            "transformed_text": transformed_text
        }), 200

    except Exception as e:
        return jsonify({"error": f"서버 통신 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
