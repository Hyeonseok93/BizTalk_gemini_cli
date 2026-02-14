import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq
from persona_manager import PersonaManager

# 환경 변수 로드
load_dotenv()

app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)  # 프론트엔드 통신 허용

# Groq 클라이언트 초기화
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
persona_manager = PersonaManager()

@app.route('/')
def index():
    """메인 페이지 서빙"""
    return app.send_static_file('index.html')

@app.route('/api/v1/personas', methods=['GET'])
def get_personas():
    """10종 페르소나 메타데이터 반환"""
    try:
        personas = persona_manager.get_all_personas()
        return jsonify(personas), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/transform', methods=['POST'])
def transform_text():
    """입력 텍스트를 선택된 페르소나의 어투로 변환"""
    data = request.json
    persona_id = data.get('persona_id')
    text = data.get('text')

    if not persona_id or not text:
        return jsonify({"error": "Missing persona_id or text"}), 400

    system_prompt = persona_manager.get_persona_prompt(persona_id)
    if not system_prompt:
        return jsonify({"error": "Invalid persona_id"}), 404

    try:
        # Groq API 호출 (Llama 3 8B 사용)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": text,
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            max_tokens=500,
        )

        transformed_text = chat_completion.choices[0].message.content
        
        return jsonify({
            "persona_id": persona_id,
            "original_text": text,
            "transformed_text": transformed_text
        }), 200

    except Exception as e:
        return jsonify({"error": f"차원 통신 불안정: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
