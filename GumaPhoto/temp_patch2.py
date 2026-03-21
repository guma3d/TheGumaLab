import os

with open("frontend/script.js", "r", encoding="utf-8") as f:
    text = f.read()

# Find start of loadUnknownPhoto
start_idx = text.find("async function loadUnknownPhoto()")
if start_idx == -1:
    start_idx = text.find("async function loadUnknownPhoto(manualTargetPayload = null)")

# Find end of loadUnknownPhoto. Next block is: // 공용 제출 로직 (백엔드 우회 테스트 모드 지원)
# or  document.getElementById('fb-submit-btn')
end_idx = text.find("// 공용 제출 로직", start_idx)
if end_idx == -1:
    end_idx = text.find("document.getElementById('fb-submit-btn')", start_idx)

prefix = text[:start_idx]
suffix = text[end_idx:]

new_func = """async function loadUnknownPhoto(manualTargetPayload = null) {
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
    submitBtn.innerHTML = 'Scan by Similarity';
    
    // TempTest UI 초기화 및 메인 컨테이너 복구
    const tempTestResults = document.getElementById('fb-temptest-results');
    if(tempTestResults) tempTestResults.style.display = 'none';
    const mainContainer = document.getElementById('fb-unknown-photo-container');
    if(mainContainer) mainContainer.style.display = 'flex';
    const infoTextContainer = document.getElementById('fb-info-text-container');
    if(infoTextContainer) infoTextContainer.style.display = 'block';
    
    try {
        if (manualTargetPayload) {
            selectedFeedbackTarget = manualTargetPayload;
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
                    if(!p.location || p.location.includes("위치정보없음")) issues.push("Location");
                    if(!p.date || p.date.includes("Unknown")) issues.push("Date");
                    if(issues.length > 0) {
                        p.issue = issues[Math.floor(Math.random() * issues.length)];
                        unknownList.push(p);
                    }
                });
                
                if(unknownList.length > 0) {
                    // 무작위 1장 추출
                    const randomChoice = unknownList[Math.floor(Math.random() * unknownList.length)];
                    let mockUrl = randomChoice.url;
                    const ogUrl = mockUrl;
                    // 고해상도 말고 빠른 로딩을 위해 webp 썸네일 변환
                    const dotIndex = mockUrl.lastIndexOf('.');
                    mockUrl = dotIndex !== -1 ? mockUrl.substring(0, dotIndex) + '_' + mockUrl.substring(dotIndex + 1).toLowerCase() + '.webp' : mockUrl;
                    
                    if (!mockUrl.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) mockUrl = '/GumaPhoto' + mockUrl;
                    selectedFeedbackTarget = { id: randomChoice.id, url: mockUrl, originalUrl: ogUrl, issue: randomChoice.issue, date: randomChoice.date, location: randomChoice.location, people: randomChoice.people, face_bbox: randomChoice.face_bbox };
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
                    selectedFeedbackTarget = { id: data.id, url: mockUrl, originalUrl: ogUrl, issue: data.issue, date: data.date, location: data.location, people: data.people, face_bbox: data.face_bbox };
                } else throw new Error("All photos are perfectly categorized!");
            }
        }

        // 추출된 사진 렌더링
        // 얼굴 피드백일 경우 원본 해상도에서 Crop하기 위해 고화질 원본 매핑
        let finalSrc = selectedFeedbackTarget.url;
        if (selectedFeedbackTarget.issue === "People" && selectedFeedbackTarget.face_bbox) {
            finalSrc = selectedFeedbackTarget.originalUrl; // Use original full-res
        }
        if (!finalSrc.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) finalSrc = '/GumaPhoto' + finalSrc;
        
        imgEl.src = finalSrc;
        
        imgEl.onload = () => {
            spinner.style.display = 'none';
            imgEl.style.display = 'block';
            
            // 크롭 엔진 가동
            if (selectedFeedbackTarget.issue === "People" && selectedFeedbackTarget.face_bbox) {
                window.cropFace(imgEl, selectedFeedbackTarget.face_bbox);
            } else {
                window.cropFace(imgEl, null); // 리셋
            }
        };
        
        let badgeType = '';
        let issueWord = '';
        if (selectedFeedbackTarget.issue.includes('Date')) {
            issueWord = 'Date';
            badgeType = `<i class="fa-regular fa-calendar-xmark" style="margin-right: 4px;"></i> Date`;
        } else if (selectedFeedbackTarget.issue.includes('Location')) {
            issueWord = 'Location';
            badgeType = `<i class="fa-solid fa-location-dot" style="margin-right: 4px;"></i> Location`;
        } else if (selectedFeedbackTarget.issue.includes('People')) {
            issueWord = 'People';
            badgeType = `<i class="fa-solid fa-user-tag" style="margin-right: 4px;"></i> People`;
        } else {
            issueWord = 'Unknown';
            badgeType = `<i class="fa-solid fa-circle-exclamation" style="margin-right: 4px;"></i> ${selectedFeedbackTarget.issue}`;
        }
        
        let restText = selectedFeedbackTarget.issue.replace(issueWord, '').trim();
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
            const t = selectedFeedbackTarget;
            
            // 1. Date
            let dateVal = (t.date && t.date.trim() !== '') ? t.date : 'Unknown';
            if (dateVal === 'Unknown Date') dateVal = 'Unknown';
            if (dateVal.length > 10 && dateVal !== 'Unknown') dateVal = dateVal.substring(0, 10);
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
                    let pStr = window.formatPeopleBadge(t.people);
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
        const guideEl = document.getElementById('fb-people-guide');
        if(selectedFeedbackTarget.issue.includes('Date')) {
            inputVal.style.display = 'none';
            inputDate.style.display = 'block';
            if (guideEl) guideEl.style.display = 'none';
        } else {
            inputDate.style.display = 'none';
            inputVal.style.display = 'block';
            if(selectedFeedbackTarget.issue.includes('People')) {
                inputVal.placeholder = "e.g. John (First name only)";
                if (guideEl) guideEl.style.display = 'block';
            } else {
                inputVal.placeholder = "e.g. Hawaii (Event or Country-State)";
                if (guideEl) guideEl.style.display = 'none';
            }
        }
        
        // [다이내믹 UI 체인지] 인물 피드백일 경우에만 'No Person / Unidentifiable' 버튼 그룹 노출
        const personBtnContainer = document.getElementById('fb-person-feedback-buttons');
        if (personBtnContainer) {
            if (selectedFeedbackTarget.issue === "People") {
                personBtnContainer.style.display = 'flex'; // 인물일 때만 컨테이너 보이기
            } else {
                personBtnContainer.style.display = 'none'; // 나머지일 때 숨기기
            }
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

"""

if "manualTargetPayload =" not in prefix:
    text = prefix + new_func + suffix
    with open("frontend/script.js", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS")
else:
    print("ALREADY PATCHED")
