class ThemeEngine {
    constructor() {
        this.root = document.documentElement;
    }

    /**
     * 페르소나 정보를 바탕으로 테마 적용
     * @param {Object} persona 
     */
    applyTheme(persona) {
        console.log(`Applying theme: ${persona.name}`);
        
        // 1. 차원 전이 글리치 효과 트리거
        this.triggerGlitchEffect();

        // 2. data-theme 속성 변경 (themes.css의 변수들이 즉시 적용됨)
        document.body.dataset.theme = persona.id;
        
        // 3. 개별 변수 보정 (필요 시)
        this.root.style.setProperty('--persona-font', persona.font);
        
        // 4. 가독성을 위한 텍스트 색상 보정은 이제 CSS에서 처리되지만, 
        // 추가적인 JS 로직이 필요할 경우 여기서 수행
    }

    /**
     * 테마 전환 시 Glitch 효과 노출
     */
    triggerGlitchEffect() {
        const body = document.body;
        body.classList.remove('glitching');
        void body.offsetWidth; // Force reflow
        body.classList.add('glitching');
        
        setTimeout(() => {
            body.classList.remove('glitching');
        }, 300);
    }
}
