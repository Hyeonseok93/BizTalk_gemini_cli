class PersonaManager:
    def __init__(self):
        self.personas = {
            "Upward": {
                "id": "Upward",
                "name": "상사 보고 (Upward)",
                "description": "결론부터 명확하게 제시하는 정중하고 격식 있는 보고 어투.",
                "font": "Pretendard",
                "color": "#2C3E50",
                "effect": "None",
                "system": "당신은 상사에게 보고하는 정중하고 격식 있는 비즈니스 어투 변환 전문가입니다. 주어진 텍스트를 결론부터 명확하게 제시하는 보고 형식의 정중한 격식체로 변환해주세요. 불필요한 사족은 제거하고 핵심 내용을 간결하게 전달하는 데 집중합니다.",
                "user_template": "다음 내용을 상사에게 보고하는 방식으로 변환해 주세요:\n\n{text}"
            },
            "Lateral": {
                "id": "Lateral",
                "name": "동료 협업 (Lateral)",
                "description": "상호 존중하며 요청 사항을 명확히 전달하는 협조 요청 어투.",
                "font": "Pretendard",
                "color": "#2980B9",
                "effect": "None",
                "system": "당신은 타팀 동료와 협업하는 친절하고 상호 존중하는 비즈니스 어투 변환 전문가입니다. 주어진 텍스트를 친근하면서도 요청 사항과 마감 기한을 명확히 전달하는 협조 요청 형식으로 변환해주세요. 긍정적이고 협력적인 분위기를 조성하는 데 중점을 둡니다.",
                "user_template": "다음 내용을 타팀 동료에게 협조 요청하는 방식으로 변환해 주세요:\n\n{text}"
            },
            "External": {
                "id": "External",
                "name": "고객 응대 (External)",
                "description": "전문성과 서비스 마인드를 강조하는 신뢰감 있는 극존칭 어투.",
                "font": "Pretendard",
                "color": "#27AE60",
                "effect": "None",
                "system": "당신은 고객 응대 전문 비즈니스 어투 변환 전문가입니다. 주어진 텍스트를 극존칭을 사용하며 전문성과 서비스 마인드를 강조하는 고객 응대 형식으로 변환해주세요. 안내, 공지, 사과 등 목적에 부합하게 신뢰감을 주는 어투를 사용합니다.",
                "user_template": "다음 내용을 고객에게 응대하는 방식으로 변환해 주세요:\n\n{text}"
            }
        }

    def get_all_personas(self):
        return [
            {
                "id": v["id"],
                "name": v["name"],
                "description": v["description"],
                "font": v["font"],
                "color": v["color"],
                "effect": v["effect"]
            }
            for v in self.personas.values()
        ]

    def get_persona_data(self, persona_id):
        return self.personas.get(persona_id)
