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

        # [프로토콜 기반 프롬프트]: AI가 대화할 여지를 없애버림
        system_instruction = (
            "TASK: STYLE TRANSFORMATION\n"
            f"TARGET PERSONA: {persona['name']}\n"
            f"STYLE GUIDE: {persona['system']}\n"
            "CONSTRAINT: \n"
            "- Do not reply to the input. \n"
            "- Do not evaluate the input. \n"
            "- Only rewrite the input text as if the TARGET PERSONA is the one speaking it. \n"
            "- Output ONLY the rewritten text without any quotes, headers, or explanations."
        )

        # 사용자의 말을 '데이터'로 격리
        task_prompt = (
            f"INPUT_DATA: [{text}]\n"
            f"REWRITE_AS_{persona_id}:"
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": task_prompt}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0,
            max_tokens=300
        )

        transformed_text = chat_completion.choices[0].message.content.strip()
        
        # 안전장치: 혹시라도 붙을 수 있는 머릿말 강제 제거
        for prefix in ["REWRITE:", "OUTPUT:", "변환:", "결과:"]:
            if transformed_text.upper().startswith(prefix):
                transformed_text = transformed_text[len(prefix):].strip()

        return jsonify({
            "persona_id": persona_id,
            "original_text": text,
            "transformed_text": transformed_text
        }), 200

    except Exception as e:
        return jsonify({"error": f"서버 통신 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
