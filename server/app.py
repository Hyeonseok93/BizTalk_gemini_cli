import os
import logging
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq, APIError
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask 애플리케이션 초기화
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'client')

app = Flask(__name__, static_folder=CLIENT_DIR, static_url_path='')
CORS(app) 

# Groq 클라이언트 초기화
groq_client = None
try:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")
    groq_client = Groq(api_key=api_key)
    logging.info("Groq client initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing Groq client: {e}")

# 대상별 프롬프트 템플릿 정의 (엄격한 제약 조건 추가)
PROMPT_TEMPLATES = {
    "Upward": {
        "id": "Upward",
        "name": "상사 보고",
        "system": (
            "당신은 비즈니스 문체 변환기입니다. 아래 규칙을 반드시 지키십시오:\n"
            "1. 원문의 '핵심 의미'만 정중하고 격식 있는 보고 체계로 변환하십시오.\n"
            "2. 원문에 없는 내용을 임의로 지어내거나 추가 정보를 덧붙이지 마십시오.\n"
            "3. 인사는 상황에 맞게 한 문장 이내로 최소화하십시오.\n"
            "4. 사족 없이 변환된 결과만 즉시 출력하십시오."
        ),
        "user_template": "다음 내용을 상사 보고용 격식체로 변환:\n{text}"
    },
    "Lateral": {
        "id": "Lateral",
        "name": "동료 협업",
        "system": (
            "당신은 비즈니스 문체 변환기입니다. 아래 규칙을 반드시 지키십시오:\n"
            "1. 원문의 의미를 타팀 동료에게 전달하는 친근하고 상호 존중하는 문체로 변환하십시오.\n"
            "2. 새로운 요청 사항이나 일정을 임의로 만들지 마십시오. 오직 입력된 텍스트만 처리하십시오.\n"
            "3. 군더더기 없이 깔끔하게 변환된 결과만 출력하십시오."
        ),
        "user_template": "다음 내용을 동료 협업용 문체로 변환:\n{text}"
    },
    "External": {
        "id": "External",
        "name": "고객 응대",
        "system": (
            "당신은 비즈니스 문체 변환기입니다. 아래 규칙을 반드시 지키십시오:\n"
            "1. 원문의 내용을 서비스 마인드가 담긴 전문적인 고객 응대용 극존칭 문구로 변환하십시오.\n"
            "2. 고객에게 보내는 안내문 형식을 취하되, 원문의 범위를 벗어나는 내용을 지어내지 마십시오.\n"
            "3. 오직 변환된 문장만 한 줄로 출력하십시오."
        ),
        "user_template": "다음 내용을 고객 응대용 극존칭 문구로 변환:\n{text}"
    }
}

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/personas', methods=['GET'])
def get_personas():
    return jsonify(list(PROMPT_TEMPLATES.values())), 200

@app.route('/api/convert', methods=['POST'])
def convert_text():
    if groq_client is None:
        return jsonify({"error": "서비스 준비 중입니다."}), 503

    data = request.json
    original_text = data.get('text')
    target = data.get('target')

    if not original_text or not target:
        return jsonify({"error": "텍스트와 변환 대상은 필수입니다."}), 400

    if target not in PROMPT_TEMPLATES:
        return jsonify({"error": "유효하지 않은 변환 대상입니다."}), 400

    prompt_data = PROMPT_TEMPLATES[target]

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt_data["system"]},
                {"role": "user", "content": prompt_data["user_template"].format(text=original_text)},
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1, # 창의성을 거의 배제하여 딴소리 방지
            max_tokens=200,
        )
        converted_text = chat_completion.choices[0].message.content.strip()
        
        # 따옴표 제거 및 첫 줄만 추출 (안전장치)
        converted_text = converted_text.replace("\"", "").split('\n')[0].strip()
        
        return jsonify({
            "original_text": original_text,
            "transformed_text": converted_text,
            "target": target
        }), 200

    except APIError as e:
        return jsonify({"error": f"AI 서비스 오류: {e.code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
