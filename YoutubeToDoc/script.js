document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('url-form');
    const input = document.getElementById('youtube-url');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const loader = submitBtn.querySelector('.loader');

    const statusContainer = document.getElementById('status-container');
    const progressFill = document.getElementById('progress-fill');
    const statusText = document.getElementById('status-text');
    const progressPercent = document.getElementById('progress-percent');

    const resultContainer = document.getElementById('result-container');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const url = input.value.trim();
        if (!url) return;

        // UI 상태 변경: 처리 중
        input.disabled = true;
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'block';

        resultContainer.classList.add('hidden');
        statusContainer.classList.remove('hidden');

        // 초기화
        updateProgress(5, '서버에 분석 요청 중...');

        try {
            // 서버에 POST 요청
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (data.success) {
                updateProgress(30, '요청 접수 완료! 영상 분석을 준비하고 있습니다.');

                // 실제 서비스에서는 여기서 1초마다 상태를 폴링(Polling)하거나
                // SSE(Server-Sent Events)를 통해 /status를 지속적으로 호출해 상태 업데이트를 받습니다.

                // 데모 목적으로 가짜 진행률 애니메이션 추가
                simulateProcessing();
            } else {
                throw new Error(data.message || '요청 처리에 실패했습니다.');
            }
        } catch (error) {
            handleError(error.message);
        }
    });

    function updateProgress(percent, text) {
        progressFill.style.width = `${percent}%`;
        progressPercent.textContent = `${percent}%`;
        statusText.textContent = text;

        if (percent >= 100) {
            setTimeout(showResult, 800);
        }
    }

    function handleError(errMsg) {
        statusText.textContent = `에러 발생: ${errMsg}`;
        statusText.style.color = '#ff4d4d';
        progressFill.style.backgroundColor = '#ff4d4d';
        progressPercent.textContent = 'Failed';

        // 입력창 복구
        resetButton();
    }

    function showResult() {
        statusContainer.classList.add('hidden');
        resultContainer.classList.remove('hidden');
        resetButton();
        input.value = ''; // 입력창 초기화
    }

    function resetButton() {
        input.disabled = false;
        submitBtn.disabled = false;
        btnText.style.display = 'block';
        loader.style.display = 'none';
    }

    // 가짜 진행률 체이닝 (데모용)
    function simulateProcessing() {
        setTimeout(() => updateProgress(45, '오디오 파형을 추출 중...'), 1500);
        setTimeout(() => updateProgress(65, 'AI가 텍스트를 인지하고 요약 중... (시간이 걸릴 수 있습니다)'), 3500);
        setTimeout(() => updateProgress(85, '최종 문서 렌더링 중...'), 6000);
        setTimeout(() => updateProgress(100, '변환 완료!'), 7500);
    }
});
