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
        
        // CSS Variables 교체
        this.root.style.setProperty('--theme-bg', persona.color);
        this.root.style.setProperty('--persona-font', persona.font);
        
        // 텍스트 가독성을 위한 배경색에 따른 글자색 자동 조정 (단순화)
        const isDark = this.isColorDark(persona.color);
        this.root.style.setProperty('--theme-text', isDark ? '#ffffff' : '#121212');
        
        // 글리치 효과 트리거 (0.3초)
        this.triggerGlitchEffect();
    }

    /**
     * 배경색의 밝기를 판단하여 글자색 결정
     * @param {string} hex 
     */
    isColorDark(hex) {
        if (!hex || hex.length < 6) return true;
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        return brightness < 128;
    }

    /**
     * 테마 전환 시 Glitch 효과 노출
     */
    triggerGlitchEffect() {
        const body = document.body;
        body.classList.add('glitching');
        setTimeout(() => {
            body.classList.remove('glitching');
        }, 300);
    }
}
