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

        # [생성형 AI의 강점을 극대화하는 몰입형 프롬프트]
        system_instruction = (
            f"너는 지금부터 '{persona['name']}' 그 자체가 되어야 한다.\n"
            f"성격 및 말투 가이드: {persona['system']}\n\n"
            "### [미션] ###\n"
            "1. 입력된 문장의 '의미'와 '의도'를 파악해라.\n"
            "2. 그 의미를 유지한 채, 네가 정한 캐릭터의 말투로 완전히 새롭게 창작해서 말해라.\n"
            "3. 만약 입력이 '질문'이라면, 사용자의 질문에 대답(Answer)하지 말고, 네 캐릭터가 그 질문을 스스로에게 혹은 세상에 던지는 식으로 '재진술(Rephrase)'해라.\n"
            "4. 절대 대화하지 마라. 오직 변환된 캐릭터의 독백 혹은 선언만 출력해라.\n"
            "5. 따옴표, 머릿말, 설명은 일절 생략하고 오직 결과 문장만 내뱉어라."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"입력된 원문: {text}\n너의 캐릭터로 변환된 문장:"}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.8,  # 창의성 복구: 매번 조금씩 다른 생생한 답변 생성
            max_tokens=300
        )

        transformed_text = chat_completion.choices[0].message.content.strip()
        
        # 안전장치: 불필요한 따옴표 제거
        transformed_text = transformed_text.replace("\"", "").replace("'", "").strip()

        return jsonify({
            "persona_id": persona_id,
            "original_text": text,
            "transformed_text": transformed_text
        }), 200

    except Exception as e:
        return jsonify({"error": f"서버 통신 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
