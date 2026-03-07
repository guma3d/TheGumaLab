document.addEventListener('DOMContentLoaded', () => {
    // 동적 경로 적용 (Nginx 하위 도메인/폴더 라우팅 지원)
    const BASE_URL = window.location.pathname.endsWith('/') ? window.location.pathname : window.location.pathname + '/';

    // 페이지 진입 시 이전 작업 내역 로드
    loadAllTasks();

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
        updateProgress(5, 'Requesting analysis from server...');

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
                updateProgress(10, 'Request received! Task queued.');

                // data.task_id를 이용해 폴링 시작
                startPolling(data.task_id);
            } else {
                throw new Error(data.error || data.message || 'Failed to process request.');
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
        statusText.textContent = `Error: ${errMsg}`;
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
                <button onclick="window.open('${BASE_URL}view/${taskId}/summary', '_blank')" class="btn primary">📄 View Summary</button>
                <button onclick="window.open('${BASE_URL}view/${taskId}/detail', '_blank')" class="btn" style="background: rgba(255, 255, 255, 0.2)">📋 View Details</button>
                <button onclick="window.location.href='${BASE_URL}download/${taskId}'" class="btn" style="background: rgba(255, 255, 255, 0.2)">⬇️ Download ZIP Archive</button>
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
                    const progressText = data.progress || 'Processing...';

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
                        updateProgress(100, 'Conversion complete!');
                        setTimeout(() => showResult(taskId), 1000);
                    } else if (status === 'failed' || status === 'interrupted' || status === 'cancelled') {
                        clearInterval(pollingInterval);
                        handleError(progressText || 'Processing failed');
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

    async function loadAllTasks() {
        try {
            const response = await fetch(BASE_URL + 'tasks');
            const data = await response.json();
            const grid = document.getElementById('tasks-grid');
            if (!grid) return;

            if (data && data.tasks && data.tasks.length > 0) {
                // 완료된 항목만 최신순으로 렌더링
                const completedTasks = data.tasks.filter(t => t.status === 'completed');
                if (completedTasks.length > 0) {
                    grid.innerHTML = completedTasks.map(task => createTaskCard(task)).join('');
                } else {
                    grid.innerHTML = '<p style="color: rgba(255,255,255,0.5); font-size:0.9rem;">No videos processed yet.</p>';
                }
            } else {
                grid.innerHTML = '<p style="color: rgba(255,255,255,0.5); font-size:0.9rem;">No videos processed yet.</p>';
            }
        } catch (err) {
            console.error('Failed to load tasks:', err);
        }
    }

    function createTaskCard(task) {
        const videoId = extractVideoId(task.url);
        const videoTitle = task.video_title || task.url || 'Unknown Video';
        let createdAt = task.created_at_display;
        if (!createdAt) {
            const d = new Date(task.created_at);
            createdAt = isNaN(d) ? '' : d.toLocaleString('ko-KR');
        }
        const thumbnailUrl = videoId ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg` : 'https://via.placeholder.com/320x180/000000/ffffff?text=No+Image';

        return `
            <a href="${BASE_URL}view/${task.task_id}/summary" target="_blank" class="grid-card">
                <div class="card-thumb">
                    <img src="${thumbnailUrl}" alt="Thumbnail">
                </div>
                <div class="card-content">
                    <div class="card-title">${videoTitle}</div>
                    <div class="card-meta">${createdAt}</div>
                </div>
            </a>
        `;
    }

    function extractVideoId(url) {
        if (!url) return null;
        try {
            const obj = new URL(url);
            if (obj.hostname.includes('youtube.com')) return obj.searchParams.get('v');
            if (obj.hostname.includes('youtu.be')) return obj.pathname.slice(1);
        } catch (e) { }
        return null;
    }
});
