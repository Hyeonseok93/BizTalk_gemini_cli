class ThemeEngine {
    constructor() {
        this.root = document.documentElement;
    }

    /**
     * 선택된 통신 모드에 따라 테마 적용
     * @param {Object} mode 
     */
    applyTheme(mode) {
        console.log(`Switching to mode: ${mode.name}`);
        
        // 1. 시각적 전환 효과 트리거
        this.triggerTransitionEffect();

        // 2. data-theme 속성 변경 (themes.css의 변수 적용)
        document.body.dataset.theme = mode.id;
        
        // 3. 폰트 등 세부 스타일 보정
        this.root.style.setProperty('--persona-font', mode.font || 'Pretendard');
    }

    /**
     * 모드 전환 시 부드러운 트랜지션 효과
     */
    triggerTransitionEffect() {
        const body = document.body;
        body.classList.remove('glitching'); // 기존 애니메이션 클래스 재활용 가능
        void body.offsetWidth; // Force reflow
        body.classList.add('glitching');
        
        setTimeout(() => {
            body.classList.remove('glitching');
        }, 300);
    }
}
