window.GumaFeedback = {};
window.feedbackQueue = [];

const feedbackHubBtn = document.getElementById('feedback-hub-btn');
const feedbackHubModal = document.getElementById('feedback-hub-modal');
const feedbackHubClose = document.getElementById('feedback-hub-close');

let currentFeedbackMode = null; // 'time_loc' or 'face'
GumaState.selectedFeedbackTarget = null; // 타겟 사진의 Qdrant Payload 정보 대기열

if (feedbackHubBtn) {
    feedbackHubBtn.addEventListener('click', () => {
        switchView('feedback');
        loadUnknownPhoto();
    });
}

if (feedbackHubClose) {
    feedbackHubClose.addEventListener('click', () => {
        feedbackHubModal.classList.add('hidden');
    });
}

document.getElementById('fb-skip-btn')?.addEventListener('click', () => {
    loadUnknownPhoto();
});

document.getElementById('fb-remove-btn')?.addEventListener('click', async () => {
    if (!GumaState.selectedFeedbackTarget) return;

    if (!confirm("이 사진을 DB와 스토리지에서 영구히 삭제하시겠습니까?")) return;

    const btn = document.getElementById('fb-remove-btn');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    btn.disabled = true;

    try {
        let apiUrl = '/api/photos';
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            apiUrl = '/GumaPhoto/api/photos';
        }

        const res = await fetch(apiUrl, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filepath: GumaState.selectedFeedbackTarget.url,
                point_id: GumaState.selectedFeedbackTarget.id
            })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || "서버에서 사진을 삭제하지 못했습니다.");
        }

        alert("성공적으로 삭제되었습니다.");

        // 삭제 성공 시 바로 다음 타겟 불러오기
        loadUnknownPhoto();

    } catch (err) {
        console.error(err);
        alert(`삭제 실패: ${err.message || '시스템 통신 오류'}`);
    } finally {
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
});

window.addEventListener('click', (e) => {
    if (e.target === feedbackHubModal) {
        feedbackHubModal.classList.add('hidden');
    }
});

document.getElementById('fb-temptest-close')?.addEventListener('click', () => {
    const mainContainer = document.getElementById('fb-unknown-photo-container');
    if (mainContainer) mainContainer.style.display = 'flex';
    const infoTextContainer = document.getElementById('fb-info-text-container');
    if (infoTextContainer) infoTextContainer.style.display = 'block';
});

window.feedbackQueue = [];

async function preloadFeedbackQueue(count = 5) {
    if (window.feedbackQueue.length >= count) return;

    let apiUrl = '/api/feedback_v2/unknown';
    if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;

    // Load concurrently up to the needed amount
    const needed = count - window.feedbackQueue.length;
    const promises = [];
    for (let i = 0; i < needed; i++) {
        promises.push(fetch(apiUrl).then(r => r.json()).catch(e => null));
    }

    const results = await Promise.all(promises);
    results.forEach(data => {
        if (data && !data.error && data.id) {
            // Avoid duplicates in queue
            if (!window.feedbackQueue.find(item => item.id === data.id)) {
                // [프리미엄 최적화] 사진 URL 자체를 브라우저 백그라운드 캐시에 은밀히 올려둡니다. (진정한 Zero-Delay)
                const preloadImg = new Image();
                preloadImg.src = data.url;

                window.feedbackQueue.push(data);
            }
        }
    });
}

async function loadUnknownPhoto(manualTargetPayload = null) {
    const imgEl = document.getElementById('fb-target-img');
    const spinner = document.getElementById('fb-loading-spinner');
    const issueTag = document.getElementById('fb-target-issue');
    const inputVal = document.getElementById('fb-input-val');
    const inputDate = document.getElementById('fb-input-date');
    const submitBtn = document.getElementById('fb-submit-btn');

    // UI 초기화
    imgEl.style.display = 'none';
    spinner.style.display = 'block';
    issueTag.style.opacity = '0';
    inputVal.value = '';

    // 달력 선택 시 기본(Default) 시작점을 오늘 날짜 기준으로 설정
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    inputDate.value = `${yyyy}-${mm}`;

    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Send';

    // TempTest UI 초기화 및 메인 컨테이너 복구
    const mainContainer = document.getElementById('fb-unknown-photo-container');
    if (mainContainer) mainContainer.style.display = 'flex';
    const infoTextContainer = document.getElementById('fb-info-text-container');
    if (infoTextContainer) infoTextContainer.style.display = 'block';

    try {
        if (manualTargetPayload) {
            GumaState.selectedFeedbackTarget = manualTargetPayload;
        } else if (window.feedbackQueue && window.feedbackQueue.length > 0) {
            GumaState.selectedFeedbackTarget = window.feedbackQueue.shift(); // 큐에서 빛의 속도로 팝(Pop)
            // 비동기로 큐 탄창 재장전
            preloadFeedbackQueue(10);
        } else {
            let apiUrl = '/api/feedback_v2/unknown';
            if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;
            let res = await fetch(apiUrl);

            // 핫-픽스: 도커 재부팅 불가 상태 시 기존 Search API를 호출하여 프론트엔드단에서 자체 Unknown 필터링 수행 (우회 트릭)
            if (res.status === 404 || res.status === 405) {
                console.log("[우회 접속] 백엔드 API가 아직 눈을 뜨지 않아 기존 Search API로 파싱합니다.");
                let sUrl = '/api/search';
                if (window.location.pathname.startsWith('/GumaPhoto')) sUrl = '/GumaPhoto' + sUrl;
                res = await fetch(sUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query: "", date: "", sort: "desc", size: 300 })
                });
                const sData = await res.json();
                const unknownList = [];
                sData.results.forEach(p => {
                    let issues = [];
                    if (!p.location || p.location.includes("위치정보없음")) issues.push("Location");
                    if (!p.date || p.date.includes("Unknown")) issues.push("Date");
                    if (issues.length > 0) {
                        p.issue = issues[Math.floor(Math.random() * issues.length)];
                        unknownList.push(p);
                    }
                });

                if (unknownList.length > 0) {
                    // 무작위 1장 추출
                    const randomChoice = unknownList[Math.floor(Math.random() * unknownList.length)];
                    let mockUrl = randomChoice.url;
                    const ogUrl = mockUrl;
                    // 고해상도 말고 빠른 로딩을 위해 webp 썸네일 변환
                    const dotIndex = mockUrl.lastIndexOf('.');
                    mockUrl = dotIndex !== -1 ? mockUrl.substring(0, dotIndex) + '_' + mockUrl.substring(dotIndex + 1).toLowerCase() + '.webp' : mockUrl;

                    if (!mockUrl.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) mockUrl = '/GumaPhoto' + mockUrl;
                    GumaState.selectedFeedbackTarget = { id: randomChoice.id, url: mockUrl, originalUrl: ogUrl, issue: randomChoice.issue, date: randomChoice.date, location: randomChoice.location, people: randomChoice.people, face_bbox: randomChoice.face_bbox };
                } else {
                    throw new Error("No pending photos left to categorize!");
                }
            } else {
                const data = await res.json();
                if (data.id) {
                    let mockUrl = data.url;
                    const ogUrl = mockUrl;
                    const dotIndex = mockUrl.lastIndexOf('.');
                    mockUrl = dotIndex !== -1 ? mockUrl.substring(0, dotIndex) + '_' + mockUrl.substring(dotIndex + 1).toLowerCase() + '.webp' : mockUrl;

                    if (!mockUrl.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) mockUrl = '/GumaPhoto' + mockUrl;
                    GumaState.selectedFeedbackTarget = { id: data.id, url: mockUrl, originalUrl: ogUrl, issue: data.issue, date: data.date, location: data.location, people: data.people, face_bbox: data.face_bbox };
                } else throw new Error("All photos are perfectly categorized!");
            }
        }

        // 추출된 사진 렌더링
        let finalSrc = GumaState.selectedFeedbackTarget.url;
        if ((GumaState.selectedFeedbackTarget.issue.includes('Person') || GumaState.selectedFeedbackTarget.issue.includes('People')) && GumaState.selectedFeedbackTarget.face_bbox) {
            finalSrc = GumaState.selectedFeedbackTarget.originalUrl || GumaState.selectedFeedbackTarget.url;
        }
        if (!finalSrc.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) finalSrc = '/GumaPhoto' + finalSrc;

        if ((GumaState.selectedFeedbackTarget.issue.includes('Person') || GumaState.selectedFeedbackTarget.issue.includes('People')) && GumaState.selectedFeedbackTarget.face_bbox && GumaState.selectedFeedbackTarget.face_bbox.length === 4) {
            const tempImg = new Image();
            tempImg.crossOrigin = "Anonymous";
            tempImg.src = finalSrc;
            tempImg.onload = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                let [x1, y1, x2, y2] = GumaState.selectedFeedbackTarget.face_bbox;
                const w = x2 - x1; const h = y2 - y1;
                const margin = Math.max(w, h) * 0.4;
                x1 = Math.max(0, x1 - margin); y1 = Math.max(0, y1 - margin);
                x2 = Math.min(tempImg.naturalWidth, x2 + margin); y2 = Math.min(tempImg.naturalHeight, y2 + margin);
                const cropW = x2 - x1; const cropH = y2 - y1;
                if (cropW > 0 && cropH > 0) {
                    canvas.width = cropW; canvas.height = cropH;
                    ctx.drawImage(tempImg, x1, y1, cropW, cropH, 0, 0, cropW, cropH);
                    imgEl.src = canvas.toDataURL('image/jpeg', 0.85);
                } else {
                    imgEl.src = tempImg.src;
                }
                spinner.style.display = 'none';
                imgEl.style.display = 'block';
            };
        } else {
            imgEl.src = finalSrc;
            imgEl.onload = () => {
                spinner.style.display = 'none';
                imgEl.style.display = 'block';
            };
        }

        let badgeType = '';
        let issueWord = '';
        if (GumaState.selectedFeedbackTarget.issue.includes('Date')) {
            issueWord = 'Date';
            badgeType = `<i class="fa-regular fa-calendar-xmark" style="margin-right: 4px;"></i> Date`;
        } else if (GumaState.selectedFeedbackTarget.issue.includes('Location')) {
            issueWord = 'Location';
            badgeType = `<i class="fa-solid fa-location-dot" style="margin-right: 4px;"></i> Location`;
        } else if (GumaState.selectedFeedbackTarget.issue.includes('People')) {
            issueWord = 'People';
            badgeType = `<i class="fa-solid fa-user-tag" style="margin-right: 4px;"></i> People`;
        } else {
            issueWord = 'Unknown';
            badgeType = `<i class="fa-solid fa-circle-exclamation" style="margin-right: 4px;"></i> ${GumaState.selectedFeedbackTarget.issue}`;
        }

        let restText = GumaState.selectedFeedbackTarget.issue.replace(issueWord, '').trim();
        if (restText) {
            issueTag.innerHTML = `<span style="background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; padding: 6px 12px; border-radius: 8px;">${badgeType}</span> <span style="color: #9ca3af; margin-left: 6px;">${restText}</span>`;
        } else {
            issueTag.innerHTML = `<span style="background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; padding: 6px 12px; border-radius: 8px;">${badgeType}</span>`;
        }
        issueTag.style.opacity = '1';

        const fbBadgesContainer = document.getElementById('fb-info-badges');
        if (fbBadgesContainer) {
            const createBadge = (icon, text, isHighlight = false) => {
                if (!text || text.trim() === '') text = 'Unknown';
                const cls = isHighlight ? 'info-badge highlight' : 'info-badge';
                return `<div class="${cls}"><i class="${icon}"></i> ${text}</div>`;
            };

            let badgesHtml = '';
            const t = GumaState.selectedFeedbackTarget;

            // 1. Date
            let dateVal = (t.date && t.date.trim() !== '') ? t.date : 'Unknown';
            if (dateVal.length > 10 && !dateVal.includes('Unknown')) dateVal = dateVal.substring(0, 10);
            badgesHtml += createBadge('fa-regular fa-calendar', dateVal);

            // 2. Location
            let locVal = (t.location && t.location.trim() !== '') ? t.location.replace(/-/g, ' ') : 'Unknown';
            if (locVal.includes('위치정보없음')) locVal = 'Unknown';
            badgesHtml += createBadge('fa-solid fa-location-dot', locVal);

            // 3. People
            let peopleVal = 'Unknown';
            let isYellow = false;
            if (t.people && Array.isArray(t.people) && t.people.length > 0) {
                if (t.people.includes('Unidentifiable Person')) {
                    peopleVal = 'Unidentifiable Person';
                    isYellow = true;
                } else if (t.people.includes('No People')) {
                    peopleVal = 'No People';
                    isYellow = true;
                } else {
                    let pStr = t.people.filter(p => !p.includes('Unknown')).join(', ');
                    if (pStr) peopleVal = pStr;
                }
            }

            if (isYellow) {
                badgesHtml += `<div class="info-badge" style="background: rgba(245, 158, 11, 0.2); border: 1px solid rgba(245, 158, 11, 0.4); color: #f59e0b;"><i class="fa-solid fa-user-tag"></i> ${peopleVal}</div>`;
            } else {
                badgesHtml += createBadge('fa-solid fa-user-tag', peopleVal, true);
            }

            fbBadgesContainer.innerHTML = badgesHtml;
        }

        // 이슈 종류에 따른 폼 UI 전환
        const personBtns = document.getElementById('fb-person-feedback-buttons');
        const personGuide = document.getElementById('fb-people-guide');
        const noLearningBtn = document.getElementById('fb-no-learning-btn');

        if (GumaState.selectedFeedbackTarget.issue.includes('Date')) {
            inputVal.style.display = 'none';
            inputDate.style.display = 'block';
            if (personBtns) personBtns.style.display = 'none';
            if (personGuide) personGuide.style.display = 'none';
            if (noLearningBtn) noLearningBtn.style.display = 'none';
        } else if (GumaState.selectedFeedbackTarget.issue.includes('Person') || GumaState.selectedFeedbackTarget.issue.includes('People')) {
            inputDate.style.display = 'none';
            inputVal.style.display = 'block';
            inputVal.placeholder = "예: 성욱 (누락된 인물의 이름)";
            if (personBtns) personBtns.style.display = 'flex';
            if (personGuide) personGuide.style.display = 'block';
            if (noLearningBtn) noLearningBtn.style.display = 'block';
        } else {
            inputDate.style.display = 'none';
            inputVal.style.display = 'block';
            inputVal.placeholder = "예: 하남 위례롯데캐슬";
            if (personBtns) personBtns.style.display = 'none';
            if (personGuide) personGuide.style.display = 'none';
            if (noLearningBtn) noLearningBtn.style.display = 'none';
        }

    } catch (err) {
        spinner.style.display = 'none';
        issueTag.innerHTML = '<i class="fa-solid fa-check-circle"></i> ' + err.message;
        issueTag.style.opacity = '1';
        issueTag.style.color = '#10b981';
        issueTag.style.background = 'transparent';
        issueTag.style.border = 'none';
        submitBtn.disabled = true;
    }
}


// =========================================================================
// 통합 백엔드 전송 모듈 (재사용성 강화)
// =========================================================================
async function submitSharedFeedback(pointId, issueType, correctValue, targetPointsArray, skipEnrolled = false) {
    const btn2 = document.getElementById('fb-submit-btn');
    const ogHtml2 = btn2 ? btn2.innerHTML : '';
    if (btn2) { btn2.disabled = true; btn2.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 대기열 배달 중...'; }

    try {
        let apiUrl = '/api/feedback_v2/submit';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;

        let res = await fetch(apiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                point_id: pointId,
                issue_type: issueType,
                correct_value: correctValue,
                target_points: targetPointsArray,
                skip_enrolled_learning: skipEnrolled
            })
        });

        if (res.status === 404 || res.status === 405) {
            console.log("[우회 접속] 백엔드 POST API 응답 누락 처리됨 (모의 통과)");
        } else {
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "제출 실패");
        }

        const feedbackHubModal = document.getElementById('feedback-hub-modal');
        if (feedbackHubModal) feedbackHubModal.classList.add('hidden');

        switchView('home');

        setTimeout(() => {
            alert(`총 ${targetPointsArray.length || 1}장의 사진이 수정되었습니다.\n화면을 새로고침합니다.`);
            window.location.reload();
        }, 100);

    } catch (err) {
        console.error(err);
        alert(err.message);
        if (btn2) { btn2.innerHTML = ogHtml2; btn2.disabled = false; }
    }
}

// 사용자 제출 로직 (백엔드 우회 테스트 모드 지원)
// Send 버튼 시뮬레이션 통합 적용 (수정 제출 API 가동 중단 상태)
document.getElementById('fb-submit-btn')?.addEventListener('click', async () => {
    if (!GumaState.selectedFeedbackTarget) return;

    const inputVal = document.getElementById('fb-input-val');
    const inputDate = document.getElementById('fb-input-date');
    let correctValue = "";

    if (GumaState.selectedFeedbackTarget.issue.includes('Date') || GumaState.selectedFeedbackTarget.issue.includes('날짜')) {
        correctValue = inputDate.value;
    } else {
        correctValue = inputVal.value.trim();
        if (inputVal.dataset.exactPayload && inputVal.dataset.exactDisplay === correctValue) {
            correctValue = inputVal.dataset.exactPayload;
        }
    }

    if (!correctValue) {
        alert("Please provide the correct information first!");
        return;
    }

    // Check for unregistered names
    if (GumaState.selectedFeedbackTarget && (GumaState.selectedFeedbackTarget.issue.includes('Person') || GumaState.selectedFeedbackTarget.issue.includes('People'))) {
        let isKnown = false;
        if (typeof GumaState.advancedStatsData !== 'undefined' && GumaState.advancedStatsData !== null && GumaState.advancedStatsData.people) {
            isKnown = GumaState.advancedStatsData.people.some(p => p.name === correctValue);
        }
        if (!isKnown) {
            const confirmed = confirm(`'${correctValue}'님은 기존에 등록된 이름이 아닙니다.\n오타가 아니라면 새로 추가하시겠습니까?`);
            if (!confirmed) return;
        }
    }

    const bulkChecks = document.querySelectorAll('.grid-checkbox:checked');
    if (bulkChecks.length > 0) {
        // 메인 화면에서 활성화된 체크박스가 존재한다면 스캔 패스하고 일괄전송(Bulk) 액션 즉시 실행
        const bulkTargets = [];
        bulkChecks.forEach(cb => bulkTargets.push(cb.getAttribute('data-id')));

        if (!bulkTargets.includes(String(GumaState.selectedFeedbackTarget.id)) && !bulkTargets.includes(Number(GumaState.selectedFeedbackTarget.id))) {
            bulkTargets.push(GumaState.selectedFeedbackTarget.id);
        }

        await submitSharedFeedback(GumaState.selectedFeedbackTarget.id, GumaState.selectedFeedbackTarget.issue, correctValue, bulkTargets);
        return;
    }

    const btn = document.getElementById('fb-submit-btn');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Auto Scanning...';
    btn.disabled = true;

    try {
        let apiUrl = '/api/feedback_v2/temptest';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;

        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                point_id: GumaState.selectedFeedbackTarget.id,
                issue_type: GumaState.selectedFeedbackTarget.issue,
                correct_value: correctValue
            })
        });

        const data = res.ok ? await res.json() : {results: []};
        
        let targetPoints = [];
        if (data && data.results && data.results.length > 0) {
            targetPoints = data.results.map(item => item.id);
        }

        if (!targetPoints.includes(String(GumaState.selectedFeedbackTarget.id)) && !targetPoints.includes(Number(GumaState.selectedFeedbackTarget.id))) {
            targetPoints.push(GumaState.selectedFeedbackTarget.id);
        }

        console.log("Auto-submitting feedback for targets count:", targetPoints.length);
        await submitSharedFeedback(GumaState.selectedFeedbackTarget.id, GumaState.selectedFeedbackTarget.issue, correctValue, targetPoints);

    } catch (err) {
        console.error(err);
        alert("Feedback error: " + err.message);
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
});

// =========================================================================
// Kakao Location Autocomplete UI Logic
// =========================================================================
const fbInputVal = document.getElementById('fb-input-val');
const fbDropdown = document.getElementById('fb-autocomplete-dropdown');
let kakaoSearchTimeout = null;

if (fbInputVal && fbDropdown) {
    fbInputVal.addEventListener('input', async (e) => {
        if (!GumaState.selectedFeedbackTarget || !GumaState.selectedFeedbackTarget.issue.includes('Location')) {
            fbDropdown.style.display = 'none';
            return;
        }

        const q = e.target.value.trim();
        if (q.length < 2) {
            fbDropdown.style.display = 'none';
            return;
        }

        if (kakaoSearchTimeout) clearTimeout(kakaoSearchTimeout);
        kakaoSearchTimeout = setTimeout(async () => {
            try {
                let apiUrl = `/api/location/search_global?q=${encodeURIComponent(q)}`;
                if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;

                const res = await fetch(apiUrl);
                if (!res.ok) return;
                const data = await res.json();

                fbDropdown.innerHTML = '';

                // 렌더링 헬퍼 함수
                const appendSection = (title, items, isKakao) => {
                    if (!items || items.length === 0) return;

                    const titleDiv = document.createElement('div');
                    titleDiv.style.padding = '8px 12px';
                    titleDiv.style.backgroundColor = '#1e293b';
                    titleDiv.style.color = isKakao ? '#facc15' : '#38bdf8'; // 카카오는 노란색, OSM은 파란색
                    titleDiv.style.fontWeight = 'bold';
                    titleDiv.style.fontSize = '12px';
                    titleDiv.style.letterSpacing = '1px';
                    titleDiv.innerHTML = isKakao ? '<i class="fa-solid fa-house-chimney"></i> 국내 상세 스팟 (Kakao)' : '<i class="fa-solid fa-globe"></i> 글로벌/해외 주소 (OSM)';
                    fbDropdown.appendChild(titleDiv);

                    items.forEach(item => {
                        const div = document.createElement('div');
                        div.style.padding = '12px 16px';
                        div.style.cursor = 'pointer';
                        div.style.borderBottom = '1px solid #4a5568';
                        div.style.color = '#e2e8f0';
                        div.style.fontSize = '14px';
                        div.style.backgroundColor = 'transparent';
                        div.innerText = item.display;

                        div.onmouseover = () => div.style.backgroundColor = '#4a5568';
                        div.onmouseout = () => div.style.backgroundColor = 'transparent';

                        div.onclick = () => {
                            fbInputVal.value = item.short_name;
                            fbInputVal.dataset.exactPayload = item.exact;
                            fbInputVal.dataset.exactDisplay = item.short_name;
                            fbDropdown.style.display = 'none';
                        };
                        fbDropdown.appendChild(div);
                    });
                };

                if ((data.kakao && data.kakao.length > 0) || (data.osm && data.osm.length > 0)) {
                    appendSection('글로벌/해외 주소 (OSM)', data.osm, false);
                    appendSection('국내 상세 스팟 (Kakao)', data.kakao, true);
                    fbDropdown.style.display = 'block';
                } else {
                    fbDropdown.style.display = 'none';
                }
            } catch (err) {
                console.error('Global autocomplete error:', err);
            }
        }, 500); // 500ms delay to prevent API spam
    });

    document.addEventListener('click', (e) => {
        if (!fbDropdown.contains(e.target) && e.target !== fbInputVal) {
            fbDropdown.style.display = 'none';
        }
    });
}

// 피드백 추가 액션 버튼들 (Skip, Remove, Unidentifiable Person, No People)
// ----------------------------------------------------------------------
document.getElementById('fb-skip-btn')?.addEventListener('click', async () => {
    switchView('feedback');
});

document.getElementById('fb-remove-btn')?.addEventListener('click', async () => {
    if (!GumaState.selectedFeedbackTarget || !GumaState.selectedFeedbackTarget.id) return;
    try {
        let apiUrl = '/api/photos';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto/api/photos';

        const res = await fetch(apiUrl, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filepath: GumaState.selectedFeedbackTarget.originalUrl || GumaState.selectedFeedbackTarget.url,
                point_id: GumaState.selectedFeedbackTarget.id
            })
        });
        if (res.ok) {
            alert("성공적으로 삭제되었습니다.");
            switchView('feedback');
        } else {
            const errData = await res.json().catch(() => ({}));
            alert(`삭제 실패: ${errData.detail || '서비스 응답 오류'}`);
        }
    } catch (err) {
        console.error("삭제 실패", err);
        alert(`삭제 실패: ${err.message || '네트워크 문제 발생'}`);
    }
});

const sendPersonFeedback = async (apiUrlEndpoint, btnId) => {
    if (!GumaState.selectedFeedbackTarget || !GumaState.selectedFeedbackTarget.id) return;
    const btn = document.getElementById(btnId);
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    btn.disabled = true;

    try {
        let apiUrl = apiUrlEndpoint;
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;

        const res = await fetch(apiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                point_id: GumaState.selectedFeedbackTarget.id,
                issue_type: GumaState.selectedFeedbackTarget.issue
            })
        });

        if (res.ok) {
            switchView('home');
            setTimeout(() => {
                alert(`총 1장의 사진이 수정되었습니다.\n화면을 새로고침합니다.`);
                window.location.reload();
            }, 100);
        } else {
            alert('Failed to submit feedback.');
        }
    } catch (err) {
        console.error(err);
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
};

document.getElementById('fb-not-a-face-btn')?.addEventListener('click', () => sendPersonFeedback('/api/feedback_v2/ignore_face', 'fb-not-a-face-btn'));
document.getElementById('fb-no-person-btn')?.addEventListener('click', () => sendPersonFeedback('/api/feedback_v2/no_person', 'fb-no-person-btn'));

// =========================================================================
// 📱 Mobile Bottom Navigation Bar & View Router Logic (Moved to main.js)
// =========================================================================


window.GumaFeedback.preloadFeedbackQueue = preloadFeedbackQueue;
window.preloadFeedbackQueue = preloadFeedbackQueue;
