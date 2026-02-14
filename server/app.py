import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

# 현재 디렉토리를 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from persona_manager import PersonaManager
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'server'))
    from persona_manager import PersonaManager

load_dotenv()

app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)

api_key = os.environ.get("GROQ_API_KEY")
client = None
if api_key:
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"Groq Client Init Error: {e}")

persona_manager = PersonaManager()

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

        # [AI에게 내리는 극도의 제약 조건]
        system_instruction = (
            "당신은 인공지능이 아니라, 입력된 문장의 '의미'를 유지하면서 '어투'만 특정 캐릭터로 교체하는 '텍스트 변환 엔진'입니다.\n\n"
            "### [작동 규칙] ###\n"
            f"1. 목표 페르소나: {persona['name']}\n"
            f"2. 페르소나 스타일: {persona['system']}\n"
            "3. 절대 규칙: 입력된 문장의 '주어'가 말하는 내용을 그대로 유지하십시오. (예: '나는 천재다' -> '{persona['name']}의 말투로 내가 천재임을 주장하는 문장')\n"
            "4. 금지 사항: 사용자의 문장에 대답하거나, 질문하거나, 의견을 덧붙이지 마십시오.\n"
            "5. 출력 형식: 부연 설명 없이 오직 변환된 '결과 문장'만 한 줄로 출력하십시오."
        )

        # Few-Shot 예시를 통해 '대답'이 아닌 '변환'임을 학습시킴
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": "나는 오늘 기분이 좋다."},
                {"role": "assistant", "content": "오늘따라 내 마음이 참으로 평온하고 흥겨우니, 이보다 더 좋을 순 없구려. (조선 선비 예시)"},
                {"role": "user", "content": text}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.1,  # 약간의 유연성을 주되 일관성 유지
            max_tokens=300
        )

        transformed_text = chat_completion.choices[0].message.content.strip()
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
