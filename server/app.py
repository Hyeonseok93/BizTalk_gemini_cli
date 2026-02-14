import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

# 현재 디렉토리를 경로에 추가 (Vercel 환경에서 모듈 임포트 안정성 확보)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from persona_manager import PersonaManager
except ImportError:
    # 혹시라도 경로 문제가 생길 경우를 대비한 추가 처리
    sys.path.append(os.path.join(os.getcwd(), 'server'))
    from persona_manager import PersonaManager

# 환경 변수 로드
load_dotenv()

# Vercel 배포를 위해 설정을 최소화합니다.
# 로컬 테스트 시에는 Flask가 정적 파일을 서빙할 수 있도록 static_folder를 설정합니다.
app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)

# API 키 확인
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
    """메인 페이지 서빙 (로컬 테스트용)"""
    try:
        return app.send_static_file('index.html')
    except Exception:
        return "Frontend files not found. If on Vercel, this route should be handled by vercel.json.", 404

@app.route('/api/v1/personas', methods=['GET'])
def get_personas():
    """페르소나 목록 반환"""
    try:
        personas = persona_manager.get_all_personas()
        return jsonify(personas), 200
    except Exception as e:
        print(f"Error in get_personas: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@app.route('/api/v1/transform', methods=['POST'])
def transform_text():
    """텍스트 변환 실행"""
    if not client:
        return jsonify({"error": "GROQ_API_KEY가 설정되지 않았습니다."}), 500

    try:
        data = request.json
        if not data:
            return jsonify({"error": "JSON 데이터가 없습니다."}), 400
            
        persona_id = data.get('persona_id')
        text = data.get('text')

        if not persona_id or not text:
            return jsonify({"error": "데이터가 부족합니다."}), 400

        persona = persona_manager.get_persona_data(persona_id)
        if not persona:
            return jsonify({"error": "존재하지 않는 페르소나입니다."}), 404

        # [Strict Constraint]: 부연 설명이나 "변환 결과" 같은 안내 문구를 완벽히 차단합니다.
        system_instruction = (
            f"{persona['system']}\n\n"
            "### [규칙: 절대 준수] ###\n"
            "1. 오직 변환된 결과 문장만 출력하십시오.\n"
            "2. '관찰 결과', '변환 결과입니다', '말투로 변환합니다' 등 어떠한 설명도 금지합니다.\n"
            "3. 인사말, 맺음말, 따옴표, 부연 설명을 절대 포함하지 마십시오.\n"
            "4. 단 한 단어의 사족도 없이 결과물만 즉시 출력하십시오."
        )
        user_content = f"문장: {text}\n변환:"

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.1-8b-instant", 
            temperature=0,                  
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
        print(f"Error in transform_text: {str(e)}")
        return jsonify({"error": f"서버 통신 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
