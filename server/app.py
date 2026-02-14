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

# 대상별 프롬프트 템플릿 정의 (말투의 격과 뉘앙스 강화)
PROMPT_TEMPLATES = {
    "Upward": {
        "id": "Upward",
        "name": "상사 보고",
        "system": (
            "당신은 상급자에게 업무를 전달하는 숙련된 직장인입니다.\n"
            "1. 말투: 극존칭보다는 정중하고 예의 바른 비즈니스 경어(하십시오체/해요체 혼용)를 사용하십시오.\n"
            "2. 뉘앙스: 상사를 존중하면서도 의견을 명확히 전달하는 '세련된 말투'를 구사하십시오.\n"
            "3. 금지: '보고드립니다'로만 시작하는 단조로운 패턴을 버리고, 상황에 맞게 유연하게 변환하십시오.\n"
            "4. 원문의 의도만 유지하고, 사족이나 임의의 정보는 절대 추가하지 마십시오."
        ),
        "user_template": "다음 내용을 상사에게 말씀드리는 정중한 말투로 변환:\n{text}"
    },
    "Lateral": {
        "id": "Lateral",
        "name": "동료 협업",
        "system": (
            "당신은 타팀 동료와 원활하게 소통하는 협업 전문가입니다.\n"
            "1. 말투: 상호 존중과 친근함이 느껴지는 비즈니스 경어를 사용하십시오.\n"
            "2. 뉘앙스: 부탁할 때는 부드럽게, 정보 공유는 명확하게 전달하는 협력적 어조를 취하십시오.\n"
            "3. 금지: 명령조를 피하고, 함께 일을 진행하자는 긍정적인 느낌을 담으십시오.\n"
            "4. 입력된 텍스트 외에 새로운 일정이나 사실을 지어내지 마십시오."
        ),
        "user_template": "다음 내용을 동료에게 전달하는 친절하고 협력적인 말투로 변환:\n{text}"
    },
    "External": {
        "id": "External",
        "name": "고객 응대",
        "system": (
            "당신은 신뢰감을 주는 고객 만족 서비스 전문가입니다.\n"
            "1. 말투: 극존칭(합쇼체)과 부드러운 어미를 사용하여 고객에게 신뢰와 전문성을 전달하십시오.\n"
            "2. 뉘앙스: 안내는 친절하게, 사과는 진정성 있게 표현하는 고객 중심 어조를 유지하십시오.\n"
            "3. 금지: 딱딱한 기계적 응대를 피하고, 고객이 대접받는 느낌이 들도록 정중하게 변환하십시오.\n"
            "4. 한 줄에서 세 줄 이내의 정제된 답변으로 출력하십시오."
        ),
        "user_template": "다음 내용을 고객에게 안내하는 전문적이고 정중한 말투로 변환:\n{text}"
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
            temperature=0.5, # 뉘앙스의 풍부함을 위해 온도를 약간 올림
            max_tokens=300,
        )
        converted_text = chat_completion.choices[0].message.content.strip()
        
        # 따옴표 및 불필요한 태그 제거
        converted_text = converted_text.replace("\"", "").replace("'", "").strip()
        
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
