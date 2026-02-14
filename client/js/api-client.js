class ApiClient {
    constructor(baseUrl = '/api/v1') {
        this.baseUrl = baseUrl;
    }

    /**
     * 페르소나 목록 조회
     */
    async getPersonas() {
        try {
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
