document.addEventListener('DOMContentLoaded', () => {
    // 동적 경로 적용 (Nginx 하위 도메인/폴더 라우팅 지원)
    const BASE_URL = window.location.pathname.endsWith('/') ? window.location.pathname : window.location.pathname + '/';

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
            const response = await fetch(BASE_URL + 'process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Source': 'web'
                },
                body: JSON.stringify({ url: url, force: true }) // force: true to skip duplicate checks for now
            });

            const data = await response.json();

            if (data.success) {
                updateProgress(10, '요청 접수 완료! Task를 큐에 등록했습니다.');

                // data.task_id를 이용해 폴링 시작
                startPolling(data.task_id);
            } else {
                throw new Error(data.error || data.message || '요청 처리에 실패했습니다.');
            }
        } catch (error) {
            handleError(error.message);
        }
    });

    function updateProgress(percent, text) {
        progressFill.style.width = `${percent}%`;
        progressPercent.textContent = `${percent}%`;
        statusText.textContent = text;
    }

    function handleError(errMsg) {
        statusText.textContent = `에러 발생: ${errMsg}`;
        statusText.style.color = '#ff4d4d';
        progressFill.style.backgroundColor = '#ff4d4d';
        progressPercent.textContent = 'Failed';

        // 입력창 복구
        resetButton();
    }

    function showResult(taskId) {
        statusContainer.classList.add('hidden');
        resultContainer.classList.remove('hidden');

        // 이전 결과에 있던 중복 버튼 방지용 (혹시 모를 초기화)
        let actionsHtml = `
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button onclick="window.open('${BASE_URL}view/${taskId}/summary', '_blank')" class="btn primary">📄 요약 결과 보기</button>
                <button onclick="window.open('${BASE_URL}view/${taskId}/detail', '_blank')" class="btn" style="background: rgba(255, 255, 255, 0.2)">📋 상세 리포트</button>
                <button onclick="window.location.href='${BASE_URL}download/${taskId}'" class="btn" style="background: rgba(255, 255, 255, 0.2)">⬇️ 압축 파일 다운로드</button>
            </div>
        `;
        resultContainer.innerHTML += actionsHtml;
        resetButton();
        input.value = ''; // 입력창 초기화
    }

    function resetButton() {
        input.disabled = false;
        submitBtn.disabled = false;
        btnText.style.display = 'block';
        loader.style.display = 'none';

        // 에러 상태 리셋
        progressFill.style.backgroundColor = '';
        statusText.style.color = '';
    }

    // 실제 서버 폴링 로직
    let pollingInterval = null;
    function startPolling(taskId) {
        if (pollingInterval) clearInterval(pollingInterval);

        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`${BASE_URL}task/${taskId}`);
                const data = await response.json();

                if (data && !data.error) {
                    const status = data.status;
                    const progressText = data.progress || '처리 중입니다...';

                    // 정규표현식으로 진행도(예: [3/10]) 기반 퍼센티지 대략적 계산
                    let percent = 15;
                    const match = progressText.match(/\[(\d+)\/(\d+)\]/);
                    if (match) {
                        const current = parseInt(match[1]);
                        const total = parseInt(match[2]);
                        percent = (current / total) * 100;
                    }
                    if (status === 'queued') percent = 10;
                    if (status === 'completed') percent = 100;

                    updateProgress(Math.min(percent, 99), progressText);

                    if (status === 'completed') {
                        clearInterval(pollingInterval);
                        updateProgress(100, '변환 완료!');
                        setTimeout(() => showResult(taskId), 1000);
                    } else if (status === 'failed' || status === 'interrupted' || status === 'cancelled') {
                        clearInterval(pollingInterval);
                        handleError(progressText || '처리 실패');
                    }
                } else if (data && data.error) {
                    clearInterval(pollingInterval);
                    handleError(data.error);
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 3000); // 3초마다 체크
    }
});
