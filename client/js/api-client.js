class ApiClient {
    constructor() {
        // 현재 호스트가 localhost나 127.0.0.1이면 Flask 서버(5000포트)를 사용하고,
        // 아니면(Vercel 등 배포 환경) 현재 도메인의 상대 경로를 사용합니다.
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        this.baseUrl = isLocal ? 'http://localhost:5000/api/v1' : '/api/v1';
    }

    /**
     * 페르소나 목록 조회
     */
    async getPersonas() {
        try {
            console.log(`Fetching personas from: ${this.baseUrl}/personas`);
            const response = await fetch(`${this.baseUrl}/personas`);
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API Error (${response.status}):`, errorText);
                throw new Error(`Failed to fetch personas: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Network or Parse Error fetching personas:', error);
            throw error;
        }
    }

    /**
     * 텍스트 변환 요청
     * @param {string} personaId 
     * @param {string} text 
     */
    async transformText(personaId, text) {
        try {
            const response = await fetch(`${this.baseUrl}/transform`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ persona_id: personaId, text: text }),
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
