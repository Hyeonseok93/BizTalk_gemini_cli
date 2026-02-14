class ApiClient {
    constructor() {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        // 1. 배포 환경 (Vercel 등)
        if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
            this.baseUrl = '/api/v1';
        } 
        // 2. 로컬 환경 (파일 직접 열기 또는 localhost 서버)
        else {
            this.baseUrl = 'http://localhost:5000/api/v1';
        }
        
        console.log(`ApiClient initialized with baseUrl: ${this.baseUrl}`);
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
