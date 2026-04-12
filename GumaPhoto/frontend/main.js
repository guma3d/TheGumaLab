let abortController = null;

// Search bar clear button
const searchInput = document.getElementById('search-query');
const clearBtn = document.getElementById('clear-btn');

searchInput.addEventListener('input', function () {
    clearBtn.classList.toggle('hidden', this.value.trim().length === 0);
});

clearBtn.addEventListener('click', function () {
    searchInput.value = '';
    clearBtn.classList.add('hidden');
    searchInput.focus();
});

// Initialize app on load
async function initApp() {
    GumaState.currentQuery = '';
    GumaState.currentOffset = 0;
    GumaState.currentGalleryFilter = "recent";
    GumaState.hasMore = true;
    GumaState.totalHits = 0;

    await fetchPhotos(false);

    const splashScreen = document.getElementById('splash-screen');
    if (splashScreen) {
        splashScreen.style.opacity = '0';
        setTimeout(() => splashScreen.remove(), 600);
    }

    if (typeof preloadFeedbackQueue === 'function') {
        preloadFeedbackQueue(10).catch(e => console.error("Feedback preload error:", e));
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Search form submit
document.getElementById('search-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    switchView('home');

    const query = document.getElementById('search-query').value.trim();
    GumaState.currentQuery = query;
    GumaState.currentOffset = 0;
    GumaState.hasMore = true;
    GumaState.totalHits = 0;

    await fetchPhotos(false);
});

async function fetchPhotos(isLoadMore) {
    if (GumaState.isFetching || !GumaState.hasMore) return;

    if (!isLoadMore && abortController) abortController.abort();
    abortController = new AbortController();
    const signal = abortController.signal;

    GumaState.isFetching = true;

    const metaContainer = document.getElementById('search-meta');
    const metaText = document.getElementById('meta-text');

    try {
        let apiUrl = '/api/search';
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            apiUrl = '/GumaPhoto/api/search';
        }

        if (!GumaState.currentQuery) {
            // Home timeline mode (최신 사진 표시)
            const sliderGrid = document.getElementById('gallery-grid');
            const searchGrid = document.getElementById('search-grid');
            metaContainer.classList.add('hidden');
            searchGrid.classList.add('hidden');
            sliderGrid.classList.remove('hidden');

            const timelineRes = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal,
                body: JSON.stringify({
                    query: "timeline_dummy", offset: GumaState.currentOffset, limit: GumaState.currentLimit, is_load_more: true,
                    people: [], location: "", scene: "photo"
                })
            }).then(r => r.json()).catch(err => {
                if (err.name !== 'AbortError') console.error("Timeline fetch error:", err);
                return { results: [] };
            });

            const results = timelineRes.results || [];
            GumaState.totalHits += results.length;
            if (results.length < GumaState.currentLimit) GumaState.hasMore = false;
            GumaState.currentOffset += GumaState.currentLimit;

            if (!isLoadMore) {
                sliderGrid.innerHTML = '';
                searchGrid.innerHTML = '';
            }
            window.GumaGallery.renderGallery(results, isLoadMore, 'gallery-grid', true, false);

        } else {
            // Search mode
            const requestPayload = {
                query: GumaState.currentQuery,
                offset: GumaState.currentOffset,
                limit: GumaState.currentLimit,
                is_load_more: isLoadMore,
                people: GumaState.currentPeople,
                location: GumaState.currentLocation,
                scene: GumaState.currentScene
            };

            let searchOverlay = null;
            let logTimer = null;
            let logEl = null;

            if (!isLoadMore) {
                searchOverlay = document.createElement('div');
                searchOverlay.id = 'search-blocking-overlay';
                searchOverlay.innerHTML = `
                <div style="background: rgba(0,0,0,0.4); position: fixed; top:0; left:0; right:0; bottom:0; z-index:9999; display:flex; align-items:center; justify-content:center; backdrop-filter:blur(4px);">
                    <div style="background:#1e293b; padding:25px 35px; border-radius:20px; box-shadow:0 20px 40px -10px rgba(0,0,0,0.5); display:flex; flex-direction:column; align-items:center; border:1px solid rgba(255,255,255,0.05); max-width:85%; text-align:center;">
                        <div style="position:relative; width:60px; height:60px; margin-bottom:15px;">
                            <i class="fa-solid fa-spinner fa-spin" style="font-size:2.2rem; color:#3b82f6; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);"></i>
                            <i class="fa-solid fa-wand-magic-sparkles" style="font-size:1rem; color:#60a5fa; position:absolute; top:50%; left:50%; margin-top:-2px; margin-left:2px; transform:translate(-50%,-50%);"></i>
                        </div>
                        <div id="search-log-text" style="color:#f8fafc; font-size:1.05em; font-weight:500; min-height:25px; letter-spacing:0.3px;">🔍 AI 검색엔진 준비 중...</div>
                    </div>
                </div>`;
                document.body.appendChild(searchOverlay);

                logEl = document.getElementById('search-log-text');
                const phases = [
                    "🔍 검색어 문맥을 분석하는 중...",
                    "👤 인물 및 연도 정보 필터링 완료",
                    "🧠 시각적 콘텍스트 탐색 시작...",
                    "📊 사진 데이터베이스와 매칭 중...",
                    "✨ 수천 장의 사진 확인 중..."
                ];
                let phaseIdx = 0;
                logTimer = setInterval(() => {
                    if (phaseIdx < phases.length && logEl) {
                        logEl.innerText = phases[phaseIdx];
                        logEl.animate([{ opacity: 0.2, transform: 'translateY(5px)' }, { opacity: 0.9, transform: 'translateY(0)' }], { duration: 300, fill: 'forwards', easing: 'ease-out' });
                        phaseIdx++;
                    }
                }, 400);
            }

            const res = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal,
                body: JSON.stringify(requestPayload)
            });
            const data = await res.json();

            if (logTimer) clearInterval(logTimer);

            if (!res.ok) {
                if (searchOverlay) searchOverlay.remove();
                throw new Error(data.detail || data.error || `HTTP Error ${res.status}`);
            }

            if (data.error) {
                if (searchOverlay) searchOverlay.remove();
                metaText.innerHTML = `Error: ${data.error}`;
                metaContainer.classList.remove('hidden');
            } else {
                if (searchOverlay && logEl) {
                    let peopleStr = data.people_detected?.length > 0 ? `인물=${data.people_detected.join(",")}` : "";
                    let locStr = data.location_detected ? `장소=${data.location_detected}` : "";
                    let visualStr = data.enhanced_query ? `테마=${data.enhanced_query}` : "";
                    let metaArr = [peopleStr, locStr, visualStr].filter(x => x !== "");
                    let finalLog = "✅ ";
                    if (metaArr.length > 0) finalLog += `[${metaArr.join(" ")}] 탐색 완료. `;
                    let displayHits = data.total_hits !== undefined ? data.total_hits : data.results.length;
                    if (data.total_hits > 0) finalLog += `총 ${displayHits.toLocaleString()}장 발견!`;
                    else if (data.total_hits === undefined) finalLog += `${displayHits.toLocaleString()}장 픽업!`;
                    else finalLog += `조건에 맞는 사진이 없습니다.`;

                    logEl.innerText = finalLog;
                    logEl.animate([{ opacity: 0, transform: 'scale(0.95)' }, { opacity: 1, transform: 'scale(1)' }], { duration: 400, fill: 'forwards', easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)' });
                    setTimeout(() => {
                        searchOverlay.style.opacity = '0';
                        searchOverlay.style.transition = 'opacity 0.4s ease';
                        setTimeout(() => searchOverlay.remove(), 400);
                    }, 800);
                }

                if (!isLoadMore) {
                    GumaState.currentPeople = data.people_detected || [];
                    GumaState.currentLocation = data.location_detected || "";
                    GumaState.currentScene = data.enhanced_query || "";
                }
                GumaState.totalHits += data.results.length;
                if (data.results.length < GumaState.currentLimit) GumaState.hasMore = false;
                GumaState.currentOffset += GumaState.currentLimit;

                const timelineHeader = document.getElementById('timeline-header');
                const sliderGrid = document.getElementById('gallery-grid');
                const searchGrid = document.getElementById('search-grid');
                timelineHeader.classList.add('hidden');
                sliderGrid.classList.add('hidden');
                searchGrid.classList.remove('hidden');

                if (data.fallback_triggered && !isLoadMore) {
                    metaText.innerHTML = `<span style="color:#ef4444; font-size:0.9em;">⚠️ '${GumaState.currentLocation}' 정확한 결과 없음, 유사 분위기 사진을 표시합니다.</span>`;
                    metaContainer.classList.remove('hidden');
                } else {
                    metaContainer.classList.add('hidden');
                }

                if (!isLoadMore) searchGrid.innerHTML = '';
                window.GumaGallery.renderGallery(data.results, isLoadMore, 'search-grid', true, true);
            }
        }

    } catch (err) {
        if (err.name === 'AbortError') return;
        console.error("fetchPhotos error:", err);
        document.getElementById('search-blocking-overlay')?.remove();
        metaText.innerHTML = `⚠️ 일시적으로 실패했습니다. <small>(${err.message})</small>`;
        metaContainer.classList.remove('hidden');
    } finally {
        GumaState.isFetching = false;
    }
}

// Infinite scroll (vertical - both gallery and search)
window.addEventListener('scroll', () => {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
        if (!GumaState.isFetching && GumaState.hasMore) fetchPhotos(true);
    }
});

// View switching
const views = ['home', 'feedback', 'system'];
function switchView(target) {
    if (target === 'home') window.scrollTo({ top: 0, behavior: 'smooth' });

    views.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.classList.toggle('hidden', v !== target);
    });

    // Header button active state
    document.getElementById('nav-feedback-btn')?.classList.toggle('active', target === 'feedback');
    document.getElementById('nav-system-btn')?.classList.toggle('active', target === 'system');
}

// Header nav buttons
document.getElementById('nav-feedback-btn')?.addEventListener('click', () => {
    switchView('feedback');
    loadUnknownPhoto();
});

document.getElementById('nav-system-btn')?.addEventListener('click', () => {
    switchView('system');
    fetchAdvancedStats();
});

// Upload
document.getElementById('upload-input')?.addEventListener('change', async function (e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    await executeUpload(files);
    setTimeout(() => location.reload(), 1000);
});

// Manual feedback trigger from lightbox
document.getElementById('modal-manual-feedback-btn')?.addEventListener('click', () => {
    if (!currentModalPhoto) return;

    const modalOverlay = document.createElement('div');
    modalOverlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:9999;display:flex;justify-content:center;align-items:center;';
    modalOverlay.innerHTML = `
        <div style="background:#1f242d;border:1px solid #374151;border-radius:12px;padding:24px;text-align:center;width:80%;max-width:320px;box-shadow:0 10px 30px rgba(0,0,0,0.5);">
            <h3 style="color:white;margin-top:0;font-size:1.2rem;margin-bottom:5px;"><i class="fa-solid fa-pen-to-square"></i> Manual Feedback</h3>
            <p style="color:#9ca3af;font-size:0.85rem;margin-bottom:20px;line-height:1.4;">어떤 정보를 수동으로 교정하시겠습니까?<br><small>(선택 시 피드백 화면으로 이동합니다)</small></p>
            <div style="display:flex;flex-direction:column;gap:10px;">
                <button id="manual-loc-btn" style="padding:12px;background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.4);color:#10b981;border-radius:8px;font-weight:600;cursor:pointer;"><i class="fa-solid fa-location-dot"></i> 장소 (Location)</button>
                <button id="manual-date-btn" style="padding:12px;background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.4);color:#3b82f6;border-radius:8px;font-weight:600;cursor:pointer;"><i class="fa-regular fa-calendar-xmark"></i> 날짜 (Date)</button>
                <button id="manual-cancel-btn" style="padding:12px;margin-top:10px;background:transparent;border:1px solid #4b5563;color:#9ca3af;border-radius:8px;cursor:pointer;">취소</button>
            </div>
        </div>`;
    document.body.appendChild(modalOverlay);

    const cleanupAndGo = (mode) => {
        document.body.removeChild(modalOverlay);
        if (!mode) return;

        const targetPhoto = Object.assign({}, currentModalPhoto);
        closeModal();

        let mockUrl = targetPhoto.url;
        const ogUrl = targetPhoto.original_path || mockUrl;
        const dotIndex = mockUrl.lastIndexOf('.');
        mockUrl = dotIndex !== -1 ? mockUrl.substring(0, dotIndex) + '_' + mockUrl.substring(dotIndex + 1).toLowerCase() + '.webp' : mockUrl;
        if (!mockUrl.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) mockUrl = '/GumaPhoto' + mockUrl;

        const manualTargetPayload = {
            id: targetPhoto.id, url: mockUrl, originalUrl: ogUrl,
            issue: mode, date: targetPhoto.date, location: targetPhoto.location,
            people: targetPhoto.people, face_bbox: targetPhoto.face_bbox || []
        };

        switchView('feedback');
        loadUnknownPhoto(manualTargetPayload);
    };

    document.getElementById('manual-loc-btn').onclick = () => cleanupAndGo('Location');
    document.getElementById('manual-date-btn').onclick = () => cleanupAndGo('Date');
    document.getElementById('manual-cancel-btn').onclick = () => cleanupAndGo(null);
});

// Stats modal
window.showStatsModal = function (type) {
    if (!GumaState.advancedStatsData) {
        alert("데이터를 불러오는 중입니다. 잠시 후 다시 시도해주세요.");
        return;
    }

    document.body.style.overflow = 'hidden';
    const modal = document.getElementById('stats-modal');
    const title = document.getElementById('stats-modal-title');
    const body = document.getElementById('stats-modal-body');
    body.innerHTML = '';

    let items = [];
    if (type === 'photo') {
        title.innerHTML = '<i class="fa-solid fa-images" style="color:#3b82f6;"></i> 사진 통계 세부';
        const ukDate = GumaState.advancedStatsData.dates.find(d => d.name === "Unknown Date")?.count || 0;
        const ukLoc = (GumaState.advancedStatsData.locations.find(d => d.name === "Unknown Location")?.count || 0) +
                      (GumaState.advancedStatsData.locations.find(d => d.name === "Unknown")?.count || 0);
        const ukPerson = (GumaState.advancedStatsData.people.find(p => p.name === "Unknown People")?.count || 0) +
                         (GumaState.advancedStatsData.people.find(p => p.name === "Unknown Person")?.count || 0);
        items = [
            { name: "Unknown Date", count: ukDate, pct: ((ukDate / GumaState.advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#f43f5e" },
            { name: "Unknown Location", count: ukLoc, pct: ((ukLoc / GumaState.advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#eab308" },
            { name: "Unknown People", count: ukPerson, pct: ((ukPerson / GumaState.advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#a855f7" },
            { name: "보유 인물 데이터 총 사람수", count: GumaState.advancedStatsData.known_faces_count, pct: "-", color: "#10b981", isAbs: true }
        ];
    } else if (type === 'person') {
        title.innerHTML = '<i class="fa-solid fa-users" style="color:#10b981;"></i> 인물 통계 세부';
        items = GumaState.advancedStatsData.people.map(p => ({
            name: p.name, count: p.count, pct: p.pct + "%",
            color: (p.name.includes("Unknown") || p.name.includes("Person") || p.name.includes("People")) ? "#a855f7" : "#10b981"
        }));
    } else if (type === 'location') {
        title.innerHTML = '<i class="fa-solid fa-location-dot" style="color:#eab308;"></i> 장소 통계 세부';
        items = GumaState.advancedStatsData.locations
            .filter(l => !l.name.includes("Unknown") && l.name !== "위치정보없음")
            .map(l => {
                let col = "#9ca3af";
                if (l.name.startsWith("대한민국")) col = "#3b82f6";
                else if (l.name.includes("일본")) col = "#ec4899";
                else if (/캘리포니아|네바다|뉴욕|하와이|괌|Guam/.test(l.name)) col = "#f43f5e";
                return { name: l.name, count: l.count, pct: l.pct + "%", color: col };
            });
    } else if (type === 'date') {
        title.innerHTML = '<i class="fa-regular fa-calendar-check" style="color:#f43f5e;"></i> 날짜 통계 세부';
        items = GumaState.advancedStatsData.dates
            .filter(d => !d.name.includes("Unknown"))
            .map(d => ({ name: d.name, count: d.count, pct: d.pct + "%", color: "#f43f5e" }));
    } else if (type === 'audit') {
        title.innerHTML = '<i class="fa-solid fa-list-check" style="color:#8b5cf6;"></i> 최근 피드백 기록';
        body.innerHTML = '<div style="display:flex;flex-direction:column;gap:12px;"><p style="color:#9ca3af;font-size:0.9rem;text-align:center;padding:20px 0;"><i class="fa-solid fa-spinner fa-spin"></i> 불러오는 중...</p></div>';
        modal.classList.remove('hidden');
        fetchAuditLogs().then(data => { body.innerHTML = renderAuditLogs(data); });
        return;
    }

    if (items.length === 0) {
        body.innerHTML = '<p style="color:#9ca3af;text-align:center;padding:20px;">등록된 데이터가 없습니다.</p>';
    } else {
        items.forEach(item => {
            const row = document.createElement('div');
            row.style.cssText = `display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:rgba(255,255,255,0.05);border-radius:8px;border-left:4px solid ${item.color};width:100%;box-sizing:border-box;`;
            const countStr = item.isAbs ? `${item.count.toLocaleString()} 명` : `총 ${item.count.toLocaleString()}장 / ${item.pct}`;
            row.innerHTML = `
                <span style="color:white;font-weight:500;font-size:0.9rem;flex:1;margin-right:10px;word-break:keep-all;">${item.name}</span>
                <span style="color:${item.color};font-weight:600;font-size:0.85rem;white-space:nowrap;">${countStr}</span>`;
            body.appendChild(row);
        });
    }

    modal.classList.remove('hidden');
};

// System stats
async function fetchAdvancedStats(forceRefresh = false) {
    const icon = document.getElementById('stats-refresh-icon');
    if (icon) icon.classList.add('fa-spin');

    try {
        let url = '/api/system/advanced';
        if (window.location.pathname.startsWith('/GumaPhoto')) url = '/GumaPhoto' + url;
        if (forceRefresh) url += '?force_refresh=true';

        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data.error) {
            console.error("Advanced stats error:", data.error);
            return;
        }

        GumaState.advancedStatsData = data;

        document.getElementById('stat-total-photos').textContent = (data.total_photos || 0).toLocaleString();
        document.getElementById('stat-total-people').textContent = (data.known_faces_count || 0).toLocaleString();

        const uniqueLocations = (data.locations || []).filter(l => !l.name.includes("Unknown") && l.name !== "위치정보없음").length;
        document.getElementById('stat-total-locations').textContent = uniqueLocations.toLocaleString();

        let dateRange = '-';
        if (data.min_date && data.max_date) {
            dateRange = `${data.min_date} ~ ${data.max_date}`;
        }
        document.getElementById('stat-total-dates').textContent = dateRange;
    } catch (e) {
        console.error("fetchAdvancedStats error:", e);
    } finally {
        if (icon) icon.classList.remove('fa-spin');
    }
}
window.fetchAdvancedStats = fetchAdvancedStats;

async function fetchAuditLogs() {
    try {
        let url = '/api/system/audit_logs';
        if (window.location.pathname.startsWith('/GumaPhoto')) url = '/GumaPhoto' + url;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (e) {
        console.error("fetchAuditLogs error:", e);
        return [];
    }
}

function renderAuditLogs(logs) {
    if (!logs || logs.length === 0) {
        return '<p style="color:#9ca3af;text-align:center;padding:20px;">피드백 기록이 없습니다.</p>';
    }

    return logs.map(log => {
        const before = log.before || {};
        const after = log.after || {};
        const filename = (before.filepath || after.filepath || '').split('/').pop();

        // 변경된 필드 자동 감지
        const changes = [];
        const fields = ['people', 'location', 'date'];
        for (const f of fields) {
            const bv = Array.isArray(before[f]) ? before[f].join(', ') : (before[f] || '');
            const av = Array.isArray(after[f]) ? after[f].join(', ') : (after[f] || '');
            if (bv !== av && (bv || av)) {
                const icons = { people: 'fa-user', location: 'fa-location-dot', date: 'fa-calendar' };
                const labels = { people: '인물', location: '장소', date: '날짜' };
                changes.push({ field: labels[f], icon: icons[f], old: bv || '-', new: av || '-' });
            }
        }

        if (changes.length === 0) return '';

        const changeHtml = changes.map(c => `
            <div style="display:flex;gap:8px;align-items:center;font-size:0.8rem;margin-top:4px;">
                <i class="fa-solid ${c.icon}" style="color:#8b5cf6;font-size:0.7rem;width:14px;"></i>
                <span style="color:#ef4444;text-decoration:line-through;">${c.old}</span>
                <i class="fa-solid fa-arrow-right" style="color:#4b5563;font-size:0.6rem;"></i>
                <span style="color:#10b981;font-weight:500;">${c.new}</span>
            </div>`).join('');

        return `<div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;border-left:3px solid #8b5cf6;">
            <div style="font-size:0.8rem;color:#9ca3af;margin-bottom:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${filename}"><i class="fa-solid fa-image" style="margin-right:4px;"></i>${filename}</div>
            ${changeHtml}
        </div>`;
    }).filter(x => x).join('');
}

window.switchView = switchView;
