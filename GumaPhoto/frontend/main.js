let abortController = null;
// Text Clear Logic
const searchInput = document.getElementById('search-query');
const clearBtn = document.getElementById('clear-btn');

searchInput.addEventListener('input', function () {
    if (this.value.trim().length > 0) {
        clearBtn.classList.remove('hidden');
    } else {
        clearBtn.classList.add('hidden');
    }
});

clearBtn.addEventListener('click', function () {
    searchInput.value = '';
    clearBtn.classList.add('hidden');
    searchInput.focus();
});

// Initialize Home Gallery on Load
async function initApp() {
    GumaState.currentQuery = '';
    GumaState.currentOffset = 0;
    GumaState.currentGalleryFilter = "recent";
    GumaState.hasMore = true;
    GumaState.totalHits = 0;

    // 1. 홈 갤러리 메인 데이터(타임라인) 초고속 로딩 (초기 체감속도 극대화 교차점)
    await fetchPhotos(false);

    // 2. 화면 필수 데이터가 완성되면 멋진 스플래시 애니메이션은 유지하되, 대기 없이 즉각 페이드아웃 (Non-blocking UX)
    const splashScreen = document.getElementById('splash-screen');
    if (splashScreen) {
        splashScreen.style.opacity = '0';
        setTimeout(() => splashScreen.remove(), 600);
    }

    // 3. 무거운 피드백 큐 로딩은 화면이 전부 뜬 뒤에 조용히 백그라운드로 장전
    // 4. 3D 지구본 모달 진입 시 발생하는 네트워크 랙(Lag)을 박멸하기 위해, 
    // 수만 장 규모의 GeoJSON 데이터를 앱 최초 로딩 백그라운드에서 투명하게 미리 쥐고 있기 (Prefetch)
    window.__geoJsonPrefetchPromise = fetch('/api/map/geojson').then(r => r.json()).catch(e => {
        console.warn("[Prefetch] Failed to preload geojson:", e);
        return null;
    });
    if (typeof preloadFeedbackQueue === 'function') {
        preloadFeedbackQueue(10).catch(e => console.error("Feedback preload error:", e));
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Tags Logic
document.addEventListener('click', e => {
    if (e.target.classList.contains('tag-btn')) {
        document.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('tag-active', 'active'));
        e.target.classList.add('tag-active', 'active');

        GumaState.currentGalleryFilter = e.target.dataset.tag;

        // Cancel any ongoing fetches
        if (abortController) {
            abortController.abort();
        }

        GumaState.currentQuery = '';

        // Check cache!
        if (GumaState.cachedTags[GumaState.currentGalleryFilter]) {
            const c = GumaState.cachedTags[GumaState.currentGalleryFilter];
            GumaState.currentOffset = c.offset;
            GumaState.hasMore = c.GumaState.hasMore;
            GumaState.totalHits = c.GumaState.totalHits;

            document.getElementById('gallery-grid').innerHTML = '';
            document.getElementById('search-grid').innerHTML = '';
            window.GumaGallery.renderGallery(c.results, false, 'gallery-grid', false, false);
            return; // fully resolved from memory
        }

        // Reset and load tag timeline
        GumaState.currentOffset = 0;
        GumaState.hasMore = true;
        GumaState.totalHits = 0;

        // Keep height stable and show loading
        const grid = document.getElementById('gallery-grid');
        grid.style.minHeight = '144px';
        grid.innerHTML = '<div style="display:flex; justify-content:center; align-items:center; height:140px; width:100%;"><i class="fa-solid fa-spinner fa-spin" style="color:var(--text-muted);"></i></div>';

        fetchPhotos(false);
    }
});

// Preload other tags into memory
async function preloadTags() {
    const tagsToPreload = ["성욱", "준우", "지우", "송이", "recent"];
    let apiUrl = '/api/search';
    if (window.location.pathname.startsWith('/GumaPhoto')) {
        apiUrl = '/GumaPhoto/api/search';
    }

    for (let tag of tagsToPreload) {
        if (GumaState.cachedTags[tag]) continue;
        try {
            let t_query = "tag_dummy";
            let t_scene = "";
            let t_people = [tag];
            let t_limit = 50;
            if (tag === "recent") {
                t_query = "timeline_dummy";
                t_scene = "photo";
                t_people = [];
                t_limit = 20;
            }
            const res = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: t_query, offset: 0, limit: t_limit, is_load_more: true,
                    people: t_people, location: "", scene: t_scene
                })
            });
            if (res.ok) {
                const data = await res.json();
                let results = data.results || [];
                if (tag !== "recent") {
                    results = results.filter(p => p.people && p.people.length === 1 && p.people.includes(tag));
                }
                GumaState.cachedTags[tag] = {
                    results: results,
                    offset: t_limit, totalHits: results.length, hasMore: (data.results && data.results.length >= t_limit)
                };
            }
        } catch (e) { }
    }
}

// Search Modal Toggle
const searchModalBtn = document.getElementById('open-search-modal-btn');
const searchModal = document.getElementById('search-modal');
const searchModalClose = document.getElementById('search-modal-close');

if (searchModalBtn && searchModal && searchModalClose) {
    searchModalBtn.addEventListener('click', () => {
        searchModal.classList.remove('hidden');
        setTimeout(() => document.getElementById('search-query').focus(), 100);
    });

    searchModalClose.addEventListener('click', () => searchModal.classList.add('hidden'));

    // 배경 터치 시 모달 닫기 기능 완전히 삭제됨 (오타 방지용)
}

// Search Form Handler
document.getElementById('search-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    if (searchModal) searchModal.classList.add('hidden'); // 검색 실행 시 팝업 닫기

    // 어느 탭에 있든 검색을 시작하면 무조건 Home(메인 갤러리 뷰) 탭으로 강제 이동
    switchView('home');

    const query = document.getElementById('search-query').value.trim();

    GumaState.currentQuery = query; // allow empty to go back to home timeline
    GumaState.currentOffset = 0;
    GumaState.hasMore = true;
    GumaState.totalHits = 0;

    await fetchPhotos(false);
});

async function fetchPhotos(isLoadMore) {
    if (GumaState.isFetching || !GumaState.hasMore) return;

    // Setup new abort controller
    if (!isLoadMore) {
        if (abortController) abortController.abort();
    }
    abortController = new AbortController();
    const signal = abortController.signal;

    GumaState.isFetching = true;

    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const btn = document.getElementById('submit-btn');
    const metaContainer = document.getElementById('search-meta');
    const metaText = document.getElementById('meta-text');

    if (!isLoadMore) {
        btn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'block';
    }

    try {
        let apiUrl = '/api/search';
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            apiUrl = '/GumaPhoto/api/search';
        }

        if (!GumaState.currentQuery) {
            // UI HOTFIX: Bypass backend empty query bug via dynamic frontend calls
            const themesContainer = document.getElementById('themes-container');
            const timelineHeader = document.getElementById('timeline-header');
            const sliderGrid = document.getElementById('gallery-grid');
            const searchGrid = document.getElementById('search-grid');
            metaContainer.classList.add('hidden');
            searchGrid.classList.add('hidden');
            sliderGrid.classList.remove('hidden');

            if (!isLoadMore) {
                // Determine if we want themes
                let fetchThemes = (themesContainer.innerHTML === '');

                let themePromise = null;
                if (fetchThemes) {
                    let themesApiUrl = window.location.pathname.startsWith('/GumaPhoto') ? '/GumaPhoto/api/themes' : '/api/themes';
                    themesApiUrl += '?limit=9';

                    themePromise = fetch(themesApiUrl, {
                        method: 'GET',
                        signal
                    }).then(r => r.json()).then(data => data.themes || []).catch(err => {
                        if (err.name !== 'AbortError') console.error("Theme fetch error:", err);
                        return [];
                    });
                }

                // Timeline Fetch
                let t_query = "timeline_dummy";
                let t_scene = "photo";
                let t_people = [];
                let t_limit = GumaState.currentLimit;

                if (GumaState.currentGalleryFilter !== "recent") {
                    t_query = "tag_dummy";
                    t_scene = "";
                    t_people = [GumaState.currentGalleryFilter];
                    t_limit = 50; // Over-fetch to filter solo shots
                }

                const timelinePromise = fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    signal,
                    body: JSON.stringify({
                        query: t_query, offset: GumaState.currentOffset, limit: t_limit, is_load_more: true,
                        people: t_people, location: "", scene: t_scene
                    })
                }).then(async r => {
                    if (!r.ok) {
                        const errText = await r.text();
                        console.error("Timeline backend error:", r.status, errText);
                        return { results: [] };
                    }
                    return r.json();
                }).catch(err => {
                    if (err.name !== 'AbortError') console.error("Timeline fetch error:", err);
                    return { results: [] };
                });

                // 무거운 테마 패치는 백엔드 단일 통신으로 비동기 위임하고 메인 타임라인 즉각 기다림 (Blocking-Free)
                if (fetchThemes && themePromise) {
                    themePromise.then(themes => {
                        if (themes && themes.length > 0) {
                            window.GumaGallery.renderThemes(themes);
                            themesContainer.classList.remove('hidden');
                        } else {
                            themesContainer.classList.add('hidden');
                        }
                    }).catch(err => console.error("Theme background load error:", err));
                } else {
                    if (themesContainer.innerHTML !== '') {
                        themesContainer.classList.remove('hidden');
                    }
                }

                // 타임라인 데이터 결괏값을 즉시 받아 UI 해방
                const timelineRes = await timelinePromise;
                timelineHeader.classList.remove('hidden');

                let results = timelineRes.results || [];
                if (GumaState.currentGalleryFilter !== "recent") {
                    results = results.filter(p => p.people && p.people.length === 1 && p.people.includes(GumaState.currentGalleryFilter));
                }

                GumaState.totalHits += results.length;
                if (timelineRes.results && timelineRes.results.length < t_limit) GumaState.hasMore = false;
                GumaState.currentOffset += t_limit;

                if (!isLoadMore) {
                    if (!GumaState.cachedTags[GumaState.currentGalleryFilter]) {
                        GumaState.cachedTags[GumaState.currentGalleryFilter] = {
                            results: results,
                            offset: GumaState.currentOffset, totalHits: GumaState.totalHits, hasMore: GumaState.hasMore
                        };
                    }
                    sliderGrid.innerHTML = '';
                    searchGrid.innerHTML = '';
                }
                window.GumaGallery.renderGallery(results, isLoadMore, 'gallery-grid', false, false);

                // Kickoff preloading in background
                if (!window._tagsPreloaded) {
                    window._tagsPreloaded = true;
                    setTimeout(preloadTags, 1500);
                }
            } else {
                // Loading more for home timeline or tag
                let t_query = "timeline_dummy";
                let t_scene = "photo";
                let t_people = [];
                let t_limit = GumaState.currentLimit;

                if (GumaState.currentGalleryFilter !== "recent") {
                    t_query = "tag_dummy";
                    t_scene = "";
                    t_people = [GumaState.currentGalleryFilter];
                    t_limit = 50;
                }

                const res = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    signal,
                    body: JSON.stringify({
                        query: t_query, offset: GumaState.currentOffset, limit: t_limit, is_load_more: true,
                        people: t_people, location: "", scene: t_scene
                    })
                });
                const timelineRes = await res.json();
                let results = timelineRes.results || [];

                if (GumaState.currentGalleryFilter !== "recent") {
                    results = results.filter(p => p.people && p.people.length === 1 && p.people.includes(GumaState.currentGalleryFilter));
                }

                GumaState.totalHits += results.length;
                if (timelineRes.results && timelineRes.results.length < t_limit) GumaState.hasMore = false;
                GumaState.currentOffset += t_limit;
                window.GumaGallery.renderGallery(results, true, 'gallery-grid', false, false);
            }
        } else {
            // Normal Search
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
            
            // 처음 검색을 시작할 때만 전체 화면을 통제하는 로딩 모달 띄우기
            if (!isLoadMore) {
                searchOverlay = document.createElement('div');
                searchOverlay.id = 'search-blocking-overlay';
                searchOverlay.innerHTML = `
                <div style="background: rgba(0, 0, 0, 0.4); position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(4px);">
                    <div style="background: #1e293b; padding: 25px 35px; border-radius: 20px; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5); display: flex; flex-direction: column; align-items: center; border: 1px solid rgba(255,255,255,0.05); max-width: 85%; text-align: center;">
                        <div style="position:relative; width: 60px; height: 60px; margin-bottom: 15px;">
                            <i class="fa-solid fa-spinner fa-spin" style="font-size: 2.2rem; color: #3b82f6; position: absolute; top:50%; left:50%; transform: translate(-50%, -50%);"></i>
                            <i class="fa-solid fa-wand-magic-sparkles" style="font-size: 1rem; color: #60a5fa; position: absolute; top:50%; left:50%; margin-top: -2px; margin-left: 2px; transform: translate(-50%, -50%);"></i>
                        </div>
                        <div id="search-log-text" style="color: #f8fafc; font-size: 1.05em; font-weight: 500; min-height: 25px; letter-spacing: 0.3px;">🔍 AI 검색엔진 준비 중...</div>
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
                    if(phaseIdx < phases.length && logEl) {
                        logEl.innerText = phases[phaseIdx];
                        // 팡 터지는 듯한 페이드 효과
                        logEl.animate([ { opacity: 0.2, transform: 'translateY(5px)' }, { opacity: 0.9, transform: 'translateY(0)' } ], { duration: 300, fill: 'forwards', easing: 'ease-out' });
                        phaseIdx++;
                    }
                }, 400); // 0.4초마다 메시지 교체 (지루하지 않게 빠르게)
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
                    // API 응답 결과로 가짜가 아닌 '진짜' 요약 로그를 표시
                    let peopleStr = data.people_detected && data.people_detected.length > 0 ? `인물=${data.people_detected.join(",")}` : "";
                    let locStr = data.location_detected ? `장소=${data.location_detected}` : "";
                    let visualStr = data.enhanced_query ? `테마=${data.enhanced_query}` : "";
                    
                    let metaArr = [peopleStr, locStr, visualStr].filter(x => x !== "");
                    let finalLog = "✅ ";
                    if (metaArr.length > 0) {
                        finalLog += `[${metaArr.join(" ")}] 탐색 완료. `;
                    }
                    let displayHits = data.total_hits !== undefined ? data.total_hits : data.results.length;
                    
                    if (data.total_hits !== undefined && data.total_hits > 0) {
                        finalLog += `전체DB 중 총 ${displayHits.toLocaleString()}장의 사진 발견!`;
                    } else if (data.total_hits === undefined) {
                        finalLog += `초기 ${displayHits.toLocaleString()}장의 검색결과 픽업!`;
                    } else {
                        finalLog += `조건에 맞는 사진이 없습니다.`;
                    }
                    
                    logEl.innerText = finalLog;
                    logEl.animate([ { opacity: 0, transform: 'scale(0.95)' }, { opacity: 1, transform: 'scale(1)' } ], { duration: 400, fill: 'forwards', easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)' });
                    
                    // 결과를 읽을 시간(800ms)을 준 뒤 부드럽게 창을 닫음
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

                const themesContainer = document.getElementById('themes-container');
                const timelineHeader = document.getElementById('timeline-header');
                const sliderGrid = document.getElementById('gallery-grid');
                const searchGrid = document.getElementById('search-grid');
                themesContainer.classList.add('hidden');
                timelineHeader.classList.add('hidden');
                sliderGrid.classList.add('hidden');
                searchGrid.classList.remove('hidden');

                let fallbackMsg = '';
                if (data.fallback_triggered && !isLoadMore) {
                    fallbackMsg = `<span style="color:#ef4444; font-size: 0.9em; margin-top:5px; display:inline-block;">⚠️ No exact match for '${GumaState.currentLocation}', showing photos with similar atmosphere instead.</span>`;
                }

                if (fallbackMsg) {
                    metaText.innerHTML = fallbackMsg;
                    metaContainer.classList.remove('hidden');
                } else {
                    metaContainer.classList.add('hidden');
                }

                if (!isLoadMore) searchGrid.innerHTML = '';
                window.GumaGallery.renderGallery(data.results, isLoadMore, 'search-grid', true, true);
            }
        }

    } catch (err) {
        if (err.name === 'AbortError') {
            return; // Expected abort, do nothing
        }
        console.error("fetchPhotos error:", err);
        const blockedOverlay = document.getElementById('search-blocking-overlay');
        if (blockedOverlay) blockedOverlay.remove();
        
        metaText.innerHTML = `⚠️ Temporarily failed to fetch. <small>(${err.message})</small>`;
        metaContainer.classList.remove('hidden');
    } finally {
        GumaState.isFetching = false;
        if (!isLoadMore) {
            btn.disabled = false;
            btnText.style.display = 'block';
            loader.style.display = 'none';
        }
    }
}

// Infinite scroll listener
window.addEventListener('scroll', () => {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
        if (!GumaState.isFetching && GumaState.hasMore) {
            fetchPhotos(true);
        }
    }
});

// Render Home Themes

// Handle Gallery Rendering

// Infinite Scroll for Horizontal Slider Grid
document.getElementById('gallery-grid').addEventListener('scroll', (e) => {
    const el = e.target;
    // Check if scrolled near the right end
    if (el.scrollWidth - el.scrollLeft - el.clientWidth < 300) {
        fetchPhotos(true);
    }
});


// ==========================================
// Photo Modal & Feedback Logic
// ==========================================
let currentModalPhoto = null;
const photoModal = document.getElementById('photo-modal');
const modalImage = document.getElementById('modal-image');
const modalClose = document.getElementById('modal-close');
const deleteBtn = document.getElementById('modal-delete-btn');
const shareBtn = document.getElementById('modal-share-btn');
const downloadBtn = document.getElementById('modal-download-btn');
const modalInfoBadges = document.getElementById('modal-info-badges');
const modalActionsCenter = document.querySelector('.modal-actions-center');

let pzInstance = null;

// 모달창에서 이미지 클릭 시 정보 뱃지 & 액션버튼 토글 숨김 기능
modalImage.addEventListener('click', () => {
    if (modalInfoBadges) modalInfoBadges.classList.toggle('hidden');
    if (modalActionsCenter) modalActionsCenter.classList.toggle('hidden');
});

// Live Progress Monitor Logic (Moved to monitor.js)
// ---------------------------------------------------------------------------------

window.showStatsModal = function (type) {
    if (!GumaState.advancedStatsData) {
        alert("데이터를 불러오는 중입니다. 잠시 후 다시 시도해주세요.");
        return;
    }

    document.body.style.overflow = 'hidden'; // 화면 뒤 터치(스크롤) 차단

    const modal = document.getElementById('stats-modal');
    const title = document.getElementById('stats-modal-title');
    const body = document.getElementById('stats-modal-body');

    body.innerHTML = '';

    let items = [];
    if (type === 'photo') {
        title.innerHTML = '<i class="fa-solid fa-images" style="color:#3b82f6;"></i> 사진 통계 세부';

        const ukDate = GumaState.advancedStatsData.dates.find(d => d.name === "Unknown Date")?.count || 0;
        const ukLoc1 = GumaState.advancedStatsData.locations.find(d => d.name === "Unknown Location")?.count || 0;
        const ukLoc2 = GumaState.advancedStatsData.locations.find(d => d.name === "Unknown")?.count || 0;
        const ukLoc = ukLoc1 + ukLoc2;

        const ukP1 = GumaState.advancedStatsData.people.find(p => p.name === "Unknown People")?.count || 0;
        const ukP2 = GumaState.advancedStatsData.people.find(p => p.name === "Unknown Person")?.count || 0;
        const ukP3 = GumaState.advancedStatsData.people.find(p => p.name === "Unidentifiable Person")?.count || 0;
        const ukP4 = GumaState.advancedStatsData.people.find(p => p.name === "No People")?.count || 0;
        const ukPerson = ukP1 + ukP2 + ukP3 + ukP4;

        items = [
            { name: "Unknown Date", count: ukDate, pct: ((ukDate / GumaState.advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#f43f5e" },
            { name: "Unknown Location", count: ukLoc, pct: ((ukLoc / GumaState.advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#eab308" },
            { name: "Unknown Person", count: ukPerson, pct: ((ukPerson / GumaState.advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#a855f7" },
            { name: "보유 인물 데이터 총 사람수", count: GumaState.advancedStatsData.known_faces_count, pct: "-", color: "#10b981", isAbs: true }
        ];

    } else if (type === 'person') {
        title.innerHTML = '<i class="fa-solid fa-users" style="color:#10b981;"></i> 인물 통계 세부';
        items = GumaState.advancedStatsData.people
            .map(p => {
                // Unknown 계열의 색상 및 이름을 조정
                let color = "#10b981";
                if (p.name.includes("Unknown") || p.name.includes("Person") || p.name.includes("People")) {
                    color = "#a855f7";
                }
                return {
                    name: p.name,
                    count: p.count,
                    pct: p.pct + "%",
                    color: color
                };
            });

    } else if (type === 'location') {
        title.innerHTML = '<i class="fa-solid fa-location-dot" style="color:#eab308;"></i> 장소 통계 세부';
        items = GumaState.advancedStatsData.locations
            .filter(l => !l.name.includes("Unknown") && l.name !== "위치정보없음")
            .map(l => {
                let col = "#9ca3af"; // Default gray
                if (l.name.startsWith("대한민국")) col = "#3b82f6"; // Blue
                else if (l.name.includes("캘리포니아") || l.name.includes("네바다") || l.name.includes("뉴욕") || l.name.includes("하와이") || l.name.includes("애리조나") || l.name.includes("텍사스") || l.name.includes("Guam") || l.name.includes("괌")) col = "#f43f5e"; // Red (USA)
                else if (l.name.includes("일본")) col = "#ec4899"; // Pink
                else if (l.name.includes("온타리오") || l.name.includes("앨버타")) col = "#10b981"; // Green
                else if (l.name.includes("베트남") || l.name.includes("안장성")) col = "#8b5cf6"; // Purple

                return {
                    name: l.name,
                    count: l.count,
                    pct: l.pct + "%",
                    color: col
                };
            });
    } else if (type === 'date') {
        title.innerHTML = '<i class="fa-regular fa-calendar-check" style="color:#f43f5e;"></i> 날짜 통계 세부';
        items = GumaState.advancedStatsData.dates
            .filter(d => !d.name.includes("Unknown"))
            .map(d => ({
                name: d.name,
                count: d.count,
                pct: d.pct + "%",
                color: "#f43f5e"
            }));
    } else if (type === 'audit') {
        title.innerHTML = '<i class="fa-solid fa-list-check" style="color:#8b5cf6;"></i> 최근 피드백 기록 열람';
        body.innerHTML = '<div style="display: flex; flex-direction: column; gap: 12px;"><p style="color: #9ca3af; font-size: 0.9rem; text-align: center; padding: 20px 0;"><i class="fa-solid fa-spinner fa-spin"></i> 데이터 불러오는 중...</p></div>';
        modal.classList.remove('hidden');

        fetchAuditLogs().then(data => {
            body.innerHTML = renderAuditLogs(data);
        });
        return;
    }

    if (items.length === 0) {
        body.innerHTML = '<p style="color:#9ca3af; text-align:center; padding: 20px;">등록된 데이터가 없습니다.</p>';
    } else {
        items.forEach(item => {
            const row = document.createElement('div');
            row.style.cssText = `display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: rgba(255,255,255,0.05); border-radius: 8px; border-left: 4px solid ${item.color || '#3b82f6'}; width: 100%; box-sizing: border-box;`;

            const nameEl = document.createElement('span');
            nameEl.style.cssText = 'color: white; font-weight: 500; font-size: 0.9rem; flex: 1; margin-right: 10px; word-break: keep-all;';
            nameEl.innerText = item.name;

            const valEl = document.createElement('div');
            valEl.style.cssText = 'text-align: right; display: flex; flex-direction: column; white-space: nowrap;';

            const countStr = item.isAbs ? `${item.count.toLocaleString()} 명` : `총 ${item.count.toLocaleString()}장 / ${item.pct}`;

            valEl.innerHTML = `<span style="color: ${item.color || '#3b82f6'}; font-weight: 600; font-size: 0.85rem;">${countStr}</span>`;

            row.appendChild(nameEl);
            row.appendChild(valEl);
            body.appendChild(row);
        });
    }

    modal.classList.remove('hidden');
};

// ---------------------------------------------------------------------------------
// Self-Healing Feedback v2.0 Logic
// ---------------------------------------------------------------------------------
const views = ['home', 'feedback', 'map', 'system'];
function switchView(target) {
    if (target !== 'system' && window.progressPollingInterval) {
        clearInterval(window.progressPollingInterval);
        window.progressPollingInterval = null;
    }

    // When switching back to home, always scroll gently up
    if (target === 'home') window.scrollTo({ top: 0, behavior: 'smooth' });

    views.forEach(v => {
        const el = document.getElementById(v);
        if (el) {
            if (v === target) el.classList.remove('hidden');
            else el.classList.add('hidden');
        }
    });

    document.querySelectorAll('.bottom-nav .nav-item').forEach(item => {
        if (item.id === `nav-${target}-btn`) item.classList.add('active');
        else item.classList.remove('active');
    });

    // 맵 뷰 진입 시 핀치/줌/스크롤로 인해 메뉴가 튕기거나 사라지지 않도록 UI를 고정 (하드 락)
    const bottomNavRef = document.getElementById('bottom-nav');
    if (target === 'map') {
        document.body.style.overflow = 'hidden';
        if (bottomNavRef) bottomNavRef.classList.remove('nav-hidden');
        window.isMapViewActive = true;
    } else {
        document.body.style.overflow = 'auto';
        window.isMapViewActive = false;
    }
}

const bottomNav = document.getElementById('bottom-nav');
let lastScrollY = window.scrollY;

if (bottomNav) {
    window.addEventListener('scroll', () => {
        if (window.isMapViewActive) return; // 맵 화면에서는 메뉴가 숨겨지지 않도록 이벤트 강제 패스

        const currentScrollY = window.scrollY;

        if (currentScrollY <= 0) {
            bottomNav.classList.remove('nav-hidden');
        } else if (currentScrollY > lastScrollY && currentScrollY > 25) {
            bottomNav.classList.add('nav-hidden');
        } else if (currentScrollY < lastScrollY) {
            bottomNav.classList.remove('nav-hidden');
        }

        lastScrollY = currentScrollY;
    }, { passive: true });

    document.getElementById('nav-home-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        // 애플리케이션 초기 화면으로 완벽하게 되돌아가기 위해 페이지 하드 리로드 실행
        location.reload();
    });

    document.getElementById('nav-feedback-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('feedback');
        loadUnknownPhoto(); // Changed from loadFeedbackTarget to loadUnknownPhoto
    });

    document.getElementById('nav-upload-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('upload');
        // 사용자가 탭을 누르자마자 즉시 사진 앱(파일 선택창)이 열리도록 트리거
        document.getElementById('upload-input')?.click();
    });

    document.getElementById('nav-map-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('map');
    });

    document.getElementById('nav-system-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('system');
        fetchAdvancedStats(); // fetch system status when tab is opened
    });
}

// =========================================================================
// Upload View Local Preview & Execution
// =========================================================================
document.getElementById('upload-input')?.addEventListener('change', async function (e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // 파일이 선택되면 화면 전환이나 프리뷰 없이 즉시 서버로 업로드 파이프라인 가동
    await executeUpload(files);

    // 업로드가 끝나면 무조건 홈 화면으로 리셋 (새로 추가된 사진 반영)
    setTimeout(() => {
        location.reload();
    }, 1000);
});


// ---------------------------------------------------------------------------------
// Manual Feedback Trigger Flow (수동 피드백 진입 모달창 연결)
// ---------------------------------------------------------------------------------
document.getElementById('modal-manual-feedback-btn')?.addEventListener('click', () => {
    if (!currentModalPhoto) return;

    // 모바일 친화적인 Z-인덱스 팝업 생성
    const modalOverlay = document.createElement('div');
    modalOverlay.style.position = 'fixed';
    modalOverlay.style.top = '0'; modalOverlay.style.left = '0';
    modalOverlay.style.width = '100%'; modalOverlay.style.height = '100%';
    modalOverlay.style.background = 'rgba(0,0,0,0.85)';
    modalOverlay.style.zIndex = '9999';
    modalOverlay.style.display = 'flex';
    modalOverlay.style.justifyContent = 'center';
    modalOverlay.style.alignItems = 'center';

    modalOverlay.innerHTML = `
        <div style="background: #1f242d; border: 1px solid #374151; border-radius: 12px; padding: 24px; text-align: center; width: 80%; max-width: 320px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <h3 style="color: white; margin-top: 0; font-size: 1.2rem; margin-bottom: 5px;"><i class="fa-solid fa-pen-to-square"></i> Manual Feedback</h3>
            <p style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 20px; line-height: 1.4;">어떤 정보를 수동으로 교정하시겠습니까?<br><small>(선택 시 피드백 화면으로 강제 이동합니다)</small></p>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <button id="manual-loc-btn" style="padding: 12px; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #10b981; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s;"><i class="fa-solid fa-location-dot"></i> 장소 (Location)</button>
                <button id="manual-date-btn" style="padding: 12px; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4); color: #3b82f6; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s;"><i class="fa-regular fa-calendar-xmark"></i> 날짜 (Date)</button>
                <button id="manual-cancel-btn" style="padding: 12px; margin-top: 10px; background: transparent; border: 1px solid #4b5563; color: #9ca3af; border-radius: 8px; cursor: pointer; transition: 0.2s;">취소 (Cancel)</button>
            </div>
        </div>
    `;

    document.body.appendChild(modalOverlay);

    // 이벤트 리스너 바인딩 헬퍼
    const cleanupAndGo = (mode) => {
        document.body.removeChild(modalOverlay);
        if (!mode) return;

        // 메모리에 글로벌 복사본을 먼저 떠둠 (closeModal 시 currentModalPhoto가 null로 타버리기 때문)
        const targetPhoto = Object.assign({}, currentModalPhoto);

        // 사진 모달창 완전 닫기
        closeModal();

        let mockUrl = targetPhoto.url;
        const ogUrl = targetPhoto.original_path || mockUrl;
        const dotIndex = mockUrl.lastIndexOf('.');
        mockUrl = dotIndex !== -1 ? mockUrl.substring(0, dotIndex) + '_' + mockUrl.substring(dotIndex + 1).toLowerCase() + '.webp' : mockUrl;
        if (!mockUrl.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) mockUrl = '/GumaPhoto' + mockUrl;

        // 타겟 객체 포장
        const manualTargetPayload = {
            id: targetPhoto.id,
            url: mockUrl,
            originalUrl: ogUrl,
            issue: mode,
            date: targetPhoto.date,
            location: targetPhoto.location,
            people: targetPhoto.people,
            face_bbox: targetPhoto.face_bbox || []
        };

        // 피드백 뷰 전환 및 주입식 화면 렌더링 호출
        switchView('feedback');
        loadUnknownPhoto(manualTargetPayload);
    };

    document.getElementById('manual-loc-btn').onclick = () => cleanupAndGo('Location');
    document.getElementById('manual-date-btn').onclick = () => cleanupAndGo('Date');
    document.getElementById('manual-cancel-btn').onclick = () => cleanupAndGo(null);
});

document.getElementById('fb-no-learning-btn')?.addEventListener('click', async () => {
    if (!GumaState.selectedFeedbackTarget) return;

    const inputVal = document.getElementById('fb-input-val');
    let correctValue = inputVal.value.trim();

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

    const btn = document.getElementById('fb-no-learning-btn');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending (No Feedback)...';
    btn.disabled = true;

    try {
        await submitSharedFeedback(GumaState.selectedFeedbackTarget.id, GumaState.selectedFeedbackTarget.issue, correctValue, [GumaState.selectedFeedbackTarget.id], true);
    } catch (err) {
        console.error(err);
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
});

window.switchView = switchView;
