class ApiClient {
    constructor() {
        const hostname = window.location.hostname;
        // 로컬 환경이면 5000 포트 명시, 배포 환경이면 상대 경로 사용
        const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
        this.baseUrl = isLocal ? 'http://localhost:5000/api' : '/api';
    }

    /**
     * 변환 모드(페르소나) 목록 조회
     */
    async getPersonas() {
        try {
            const response = await fetch(`${this.baseUrl}/personas`);
            if (!response.ok) throw new Error('Failed to fetch modes');
            return await response.json();
        } catch (error) {
            console.error('Error fetching personas:', error);
            throw error;
        }
    }

    /**
     * 텍스트 변환 요청
     * @param {string} target 
     * @param {string} text 
     */
    async transformText(target, text) {
        try {
            const response = await fetch(`${this.baseUrl}/convert`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ target: target, text: text }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Transformation failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Error transforming text:', error);
            throw error;
        }
    }
}
