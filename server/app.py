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
# 'client' 디렉토리를 static 폴더로 지정합니다.
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

# 대상별 프롬프트 템플릿 정의
PROMPT_TEMPLATES = {
    "Upward": {
        "id": "Upward",
        "name": "상사 보고",
        "description": "결론부터 명확하게 제시하는 정중하고 격식 있는 보고 어투.",
        "color": "#2C3E50",
        "system": "당신은 상사에게 보고하는 정중하고 격식 있는 비즈니스 어투 변환 전문가입니다. 주어진 텍스트를 결론부터 명확하게 제시하는 보고 형식의 정중한 격식체로 변환해주세요. 불필요한 사족은 제거하고 핵심 내용을 간결하게 전달하는 데 집중합니다.",
        "user_template": "다음 내용을 상사에게 보고하는 방식으로 변환해 주세요:\n\n{text}"
    },
    "Lateral": {
        "id": "Lateral",
        "name": "동료 협업",
        "description": "타팀 동료와 협업하는 친절하고 상호 존중하는 비즈니스 어투.",
        "color": "#2980B9",
        "system": "당신은 타팀 동료와 협업하는 친절하고 상호 존중하는 비즈니스 어투 변환 전문가입니다. 주어진 텍스트를 친근하면서도 요청 사항과 마감 기한을 명확히 전달하는 협조 요청 형식으로 변환해주세요. 긍정적이고 협력적인 분위기를 조성하는 데 중점을 둡니다.",
        "user_template": "다음 내용을 타팀 동료에게 협조 요청하는 방식으로 변환해 주세요:\n\n{text}"
    },
    "External": {
        "id": "External",
        "name": "고객 응대",
        "description": "전문성과 서비스 마인드를 강조하는 신뢰감 있는 고객 응대 어투.",
        "color": "#27AE60",
        "system": "당신은 고객 응대 전문 비즈니스 어투 변환 전문가입니다. 주어진 텍스트를 극존칭을 사용하며 전문성과 서비스 마인드를 강조하는 고객 응대 형식으로 변환해주세요. 안내, 공지, 사과 등 목적에 부합하게 신뢰감을 주는 어투를 사용합니다.",
        "user_template": "다음 내용을 고객에게 응대하는 방식으로 변환해 주세요:\n\n{text}"
    }
}

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/personas', methods=['GET'])
def get_personas():
    """UI 구성을 위해 템플릿 목록 반환"""
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
            temperature=0.3,
            max_tokens=500,
        )
        converted_text = chat_completion.choices[0].message.content.strip()
        
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
