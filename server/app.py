import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq
from persona_manager import PersonaManager

# 환경 변수 로드
load_dotenv()

app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
persona_manager = PersonaManager()

@app.route('/')
def index():
    """메인 페이지 서빙"""
    return app.send_static_file('index.html')

@app.route('/api/v1/personas', methods=['GET'])
def get_personas():
    """페르소나 목록 반환"""
    try:
        return jsonify(persona_manager.get_all_personas()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/transform', methods=['POST'])
def transform_text():
    """텍스트 변환 실행"""
    data = request.json
    persona_id = data.get('persona_id')
    text = data.get('text')

    if not persona_id or not text:
        return jsonify({"error": "데이터가 부족합니다."}), 400

    persona = persona_manager.get_persona_data(persona_id)
    if not persona:
        return jsonify({"error": "존재하지 않는 페르소나입니다."}), 404

    try:
        # 시스템 지침 강화 및 사용자 템플릿 적용
        system_instruction = f"{persona['system']}\n\n[결과 제한]: 오직 변환된 문장만 출력하십시오. 설명, 인사, 따옴표 등 사족은 일절 금지합니다."
        user_content = persona['user_template'].format(text=text)

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct", # 지능이 더 높은 70B 모델 사용
            temperature=0,                  # 랜덤성 제로 (가장 기계적인 답변)
            max_tokens=300
        )

        transformed_text = chat_completion.choices[0].message.content.strip()
        
        # 불필요한 "출력:" 혹은 따옴표 제거 (안전장치)
        transformed_text = transformed_text.replace("출력:", "").replace("\"", "").strip()

        return jsonify({
            "persona_id": persona_id,
            "original_text": text,
            "transformed_text": transformed_text
        }), 200

    except Exception as e:
        return jsonify({"error": f"서버 통신 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)