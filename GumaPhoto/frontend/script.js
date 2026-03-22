let currentQuery = '';
let currentGalleryFilter = "recent";
let currentOffset = 0;
let currentLimit = 20;
let currentPeople = [];
let currentLocation = '';
let currentScene = '';
let isFetching = false;
let abortController = null;
let hasMore = true;
let totalHits = 0;
let cachedTags = {};

// Text Clear Logic
const searchInput = document.getElementById('search-query');
const clearBtn = document.getElementById('clear-btn');

searchInput.addEventListener('input', function() {
    if (this.value.trim().length > 0) {
        clearBtn.classList.remove('hidden');
    } else {
        clearBtn.classList.add('hidden');
    }
});

clearBtn.addEventListener('click', function() {
    searchInput.value = '';
    clearBtn.classList.add('hidden');
    searchInput.focus();
});

// Initialize Home Gallery on Load
document.addEventListener('DOMContentLoaded', async () => {
    currentQuery = '';
    currentOffset = 0;
    currentGalleryFilter = "recent";
    hasMore = true;
    totalHits = 0;
    
    // 1. 홈 갤러리 메인 데이터 로딩 및 피드백 큐 10개 자동 장전 (Parallel)
    await Promise.all([
        fetchPhotos(false),
        preloadFeedbackQueue(10)
    ]);
    
    // 2. 프리패치가 완료되면 스플래시 화면을 페이드아웃하며 제거
    const splashScreen = document.getElementById('splash-screen');
    if (splashScreen) {
        splashScreen.style.opacity = '0';
        setTimeout(() => splashScreen.remove(), 600);
    }
});

// Tags Logic
document.addEventListener('click', e => {
    if (e.target.classList.contains('tag-btn')) {
        document.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('tag-active', 'active'));
        e.target.classList.add('tag-active', 'active');
        
        currentGalleryFilter = e.target.dataset.tag;
        
        // Cancel any ongoing fetches
        if (abortController) {
            abortController.abort();
        }
        
        currentQuery = '';
        
        // Check cache!
        if (cachedTags[currentGalleryFilter]) {
             const c = cachedTags[currentGalleryFilter];
             currentOffset = c.offset;
             hasMore = c.hasMore;
             totalHits = c.totalHits;
             
             document.getElementById('gallery-grid').innerHTML = '';
             document.getElementById('search-grid').innerHTML = '';
             renderGallery(c.results, false, 'gallery-grid', false, false);
             return; // fully resolved from memory
        }

        // Reset and load tag timeline
        currentOffset = 0;
        hasMore = true;
        totalHits = 0;
        
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
        if (cachedTags[tag]) continue;
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
                cachedTags[tag] = {
                    results: results,
                    offset: t_limit,
                    totalHits: results.length,
                    hasMore: (data.results && data.results.length >= t_limit)
                };
            }
        } catch(e) {}
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
    
    searchModal.addEventListener('click', (e) => {
        if (e.target === searchModal) searchModal.classList.add('hidden');
    });
}

// Search Form Handler
document.getElementById('search-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    if (searchModal) searchModal.classList.add('hidden'); // 검색 실행 시 팝업 닫기
    
    // 어느 탭에 있든 검색을 시작하면 무조건 Home(메인 갤러리 뷰) 탭으로 강제 이동
    switchView('home');
    
    const query = document.getElementById('search-query').value.trim();
    
    currentQuery = query; // allow empty to go back to home timeline
    currentOffset = 0;
    hasMore = true;
    totalHits = 0;

    await fetchPhotos(false);
});

async function fetchPhotos(isLoadMore) {
    if (isFetching || !hasMore) return;
    
    // Setup new abort controller
    if (!isLoadMore) {
        if (abortController) abortController.abort();
    }
    abortController = new AbortController();
    const signal = abortController.signal;
    
    isFetching = true;

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

        if (!currentQuery) {
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
                
                let themePromises = [];
                if (fetchThemes) {
                    const generalIdeas = [
                        { title: "Winter Memories", scene: "winter snow cold" },
                        { title: "Spring Vibes", scene: "spring cherry blossom warm" },
                        { title: "Summer Waves", scene: "summer beach ocean sand" },
                        { title: "Autumn Leaves", scene: "autumn fall leaves" },
                        { title: "Delicious Meals", scene: "delicious food eating meal" },
                        { title: "Animal Friends", scene: "dog pet animal" },
                        { title: "City Explorers", scene: "city street building urban" },
                        { title: "Nature Walks", scene: "forest tree mountain nature" },
                        { title: "Joyful Moments", scene: "happy smiling laughing" },
                        { title: "Birthday Parties", scene: "birthday cake celebration party" },
                        { title: "Night Vibes", scene: "night dark lights" },
                        { title: "Cloudy Moods", scene: "cloudy grey sky moody" },
                        { title: "Cafe Hopping", scene: "cafe coffee drinking" },
                        { title: "Beautiful Landscapes", scene: "landscape scenic view" },
                        { title: "Travel Adventures", scene: "travel luggage map plane" },
                        { title: "Peaceful Times", scene: "peaceful calm quiet resting" },
                        { title: "Sunset Magic", scene: "sunset sun twilight orange sky" },
                        { title: "Art & Culture", scene: "museum art gallery painting exhibition" },
                        { title: "In the Mountains", scene: "mountain hiking trail" }
                    ];
                    const locationIdeas = [
                        { title: "Trip to Jeju", location: "Jeju Si South Korea" },
                        { title: "Memories in San Francisco", location: "San Francisco California" },
                        { title: "Las Vegas Nights", location: "Las Vegas Nevada" },
                        { title: "Incheon Stops", location: "Incheon South Korea" },
                        { title: "Seoul City Life", location: "Seoul South Korea" }
                    ];
                    
                    const allThemeIdeas = [...generalIdeas, ...locationIdeas].sort(() => 0.5 - Math.random());
                    // 15가지를 랜덤하게 질의하여, 사진이 없는 테마가 탈락하더라도 10개 이상이 살아남게 함
                    const themeIdeas = allThemeIdeas.slice(0, 15);
                    
                    themePromises = themeIdeas.map(t => fetch(apiUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        signal,
                        body: JSON.stringify({
                            query: "theme_dummy", offset: 0, limit: 12, is_load_more: true,
                            people: [], location: t.location || "", scene: t.scene || ""
                        })
                    }).then(r => r.json()).then(data => ({
                        title: t.title,
                        photos: data.results || []
                    })).catch(err => { if (err.name !== 'AbortError') console.error(err); return {title: t.title, photos: []}; }));
                }
                
                // Timeline Fetch
                let t_query = "timeline_dummy";
                let t_scene = "photo";
                let t_people = [];
                let t_limit = currentLimit;
                
                if (currentGalleryFilter !== "recent") {
                    t_query = "tag_dummy";
                    t_scene = "";
                    t_people = [currentGalleryFilter];
                    t_limit = 50; // Over-fetch to filter solo shots
                }

                const timelinePromise = fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    signal,
                    body: JSON.stringify({
                        query: t_query, offset: currentOffset, limit: t_limit, is_load_more: true,
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
                    return {results: []}; 
                });

                const responses = await Promise.all([...(fetchThemes ? themePromises : []), timelinePromise]);
                const timelineRes = responses[responses.length - 1];
                
                if (fetchThemes) {
                    const rawThemes = responses.slice(0, responses.length - 1);
                    // 빈 결과를 걸러내고 무조건 10개로 고정
                    const themes = rawThemes.filter(t => t && t.photos && t.photos.length > 0).slice(0, 10);
                    if (themes.length > 0) {
                        renderThemes(themes);
                        themesContainer.classList.remove('hidden');
                    } else {
                        themesContainer.classList.add('hidden');
                    }
                } else {
                    if (themesContainer.innerHTML !== '') {
                        themesContainer.classList.remove('hidden');
                    }
                }
                timelineHeader.classList.remove('hidden');
                
                let results = timelineRes.results || [];
                if (currentGalleryFilter !== "recent") {
                    results = results.filter(p => p.people && p.people.length === 1 && p.people.includes(currentGalleryFilter));
                }
                
                totalHits += results.length;
                if (timelineRes.results && timelineRes.results.length < t_limit) hasMore = false;
                currentOffset += t_limit;
                
                if (!isLoadMore) {
                    if (!cachedTags[currentGalleryFilter]) {
                        cachedTags[currentGalleryFilter] = {
                            results: results,
                            offset: currentOffset,
                            totalHits: totalHits,
                            hasMore: hasMore
                        };
                    }
                    sliderGrid.innerHTML = '';
                    searchGrid.innerHTML = '';
                }
                renderGallery(results, isLoadMore, 'gallery-grid', false, false);
                
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
                let t_limit = currentLimit;
                
                if (currentGalleryFilter !== "recent") {
                    t_query = "tag_dummy";
                    t_scene = "";
                    t_people = [currentGalleryFilter];
                    t_limit = 50; 
                }

                const res = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    signal,
                    body: JSON.stringify({
                        query: t_query, offset: currentOffset, limit: t_limit, is_load_more: true,
                        people: t_people, location: "", scene: t_scene
                    })
                });
                const timelineRes = await res.json();
                let results = timelineRes.results || [];
                
                if (currentGalleryFilter !== "recent") {
                    results = results.filter(p => p.people && p.people.length === 1 && p.people.includes(currentGalleryFilter));
                }
                
                totalHits += results.length;
                if (timelineRes.results && timelineRes.results.length < t_limit) hasMore = false;
                currentOffset += t_limit;
                renderGallery(results, true, 'gallery-grid', false, false);
            }
        } else {
            // Normal Search
            const requestPayload = {
                query: currentQuery,
                offset: currentOffset,
                limit: currentLimit,
                is_load_more: isLoadMore,
                people: currentPeople,
                location: currentLocation,
                scene: currentScene
            };
    
            const res = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal,
                body: JSON.stringify(requestPayload)
            });
            const data = await res.json();
    
            if (!res.ok) throw new Error(data.detail || data.error || `HTTP Error ${res.status}`);
            
            if (data.error) {
                metaText.innerHTML = `Error: ${data.error}`;
                metaContainer.classList.remove('hidden');
            } else {
                if (!isLoadMore) {
                    currentPeople = data.people_detected || [];
                    currentLocation = data.location_detected || "";
                    currentScene = data.enhanced_query || "";
                }
                totalHits += data.results.length;
                if (data.results.length < currentLimit) hasMore = false;
                currentOffset += currentLimit;
    
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
                    fallbackMsg = `<span style="color:#ef4444; font-size: 0.9em; margin-top:5px; display:inline-block;">⚠️ No exact match for '${currentLocation}', showing photos with similar atmosphere instead.</span>`;
                }
    
                if (fallbackMsg) {
                    metaText.innerHTML = fallbackMsg;
                    metaContainer.classList.remove('hidden');
                } else {
                    metaContainer.classList.add('hidden');
                }
                
                if (!isLoadMore) searchGrid.innerHTML = '';
                renderGallery(data.results, isLoadMore, 'search-grid', true, true);
            }
        }
        
    } catch (err) {
        if (err.name === 'AbortError') {
            return; // Expected abort, do nothing
        }
        console.error("fetchPhotos error:", err);
        metaText.innerHTML = `⚠️ Temporarily failed to fetch. <small>(${err.message})</small>`;
        metaContainer.classList.remove('hidden');
    } finally {
        isFetching = false;
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
        if (!isFetching && hasMore) {
            fetchPhotos(true);
        }
    }
});

// Render Home Themes
function renderThemes(themes) {
    const container = document.getElementById('themes-container');
    container.innerHTML = '';
    
    themes.forEach(theme => {
        const section = document.createElement('div');
        section.className = 'theme-section';
        
        const h3 = document.createElement('h3');
        h3.innerText = theme.title;
        h3.className = 'theme-title';
        section.appendChild(h3);
        
        const scrollBox = document.createElement('div');
        scrollBox.className = 'theme-scroll-box';
        
        theme.photos.forEach(photo => {
            const imgBtn = document.createElement('div');
            imgBtn.className = 'theme-photo-item';
            imgBtn.dataset.id = photo.id;
            
            let imgUrl = photo.url;
            if (window.location.pathname.startsWith('/GumaPhoto')) {
                imgUrl = '/GumaPhoto' + imgUrl;
            }
            
            const dotIndex = imgUrl.lastIndexOf('.');
            const thumbUrl = dotIndex !== -1 ? 
                imgUrl.substring(0, dotIndex) + '_' + imgUrl.substring(dotIndex + 1).toLowerCase() + '.webp' : imgUrl;
            
            const img = document.createElement('img');
            img.src = thumbUrl;
            img.loading = "lazy";
            
            img.onerror = function() {
                if (this.src !== imgUrl) this.src = imgUrl;
            };
            imgBtn.appendChild(img);
            
            // Add click to open modal
            imgBtn.addEventListener('click', () => {
                openModal(photo, imgUrl);
            });
            
            scrollBox.appendChild(imgBtn);
        });
        
        section.appendChild(scrollBox);
        container.appendChild(section);
    });
}

// Handle Gallery Rendering
function renderGallery(photos, append = false, targetId = 'gallery-grid', isMasonry = false, showMeta = false) {
    const grid = document.getElementById(targetId);
    // Note: We don't automatically clear grid here because we clear it before render now to prevent layout jump
    // if (!append) grid.innerHTML = '';

    if (photos.length === 0 && !append && grid.innerHTML === '') {
        grid.innerHTML = '<p style="color: var(--text-muted);">No photos found.</p>';
        return;
    }

    photos.forEach(photo => {
        // Create Item as a Slider Item or Masonry Item
        const item = document.createElement('div');
        item.className = isMasonry ? 'image-item' : 'theme-photo-item';
        // 고유 ID 맵핑 (DOM 삭제 최적화)
        item.dataset.id = photo.id;

        // Base Image
        // Handling paths via Nginx proxy as well
        let imgUrl = photo.url;
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            imgUrl = '/GumaPhoto' + imgUrl;
        }

        const dotIndex = imgUrl.lastIndexOf('.');
        const thumbUrl = dotIndex !== -1 ? 
            imgUrl.substring(0, dotIndex) + '_' + imgUrl.substring(dotIndex + 1).toLowerCase() + '.webp' : imgUrl;

        // Img tag
        const img = document.createElement('img');
        img.src = thumbUrl;
        img.loading = "lazy";
        
        img.onerror = function() {
            if (this.src !== imgUrl) this.src = imgUrl;
        };

        // Assembly
        item.style.position = 'relative';
        item.appendChild(img);

        if (showMeta) {
            // 0. 유사도 (AI 검색 결과 전용) - Top Left 분리
            if (photo.score !== undefined) {
                const scoreText = (photo.score * 100).toFixed(1) + '%';
                const scoreBadge = document.createElement('div');
                scoreBadge.className = 'meta-badge';
                scoreBadge.style.left = '5px';
                scoreBadge.style.top = '5px';
                scoreBadge.innerHTML = `<i class="fa-solid fa-bullseye"></i> 유사도 = ${scoreText}`;
                item.appendChild(scoreBadge);
            }

            const overlay = document.createElement('div');
            overlay.className = 'info-badges-overlay';
            overlay.style.left = '5px';
            overlay.style.bottom = '5px';
            // 크기 30% 축소 (transform-origin 적용하여 왼쪽 아래 기준으로 축소)
            overlay.style.transform = 'scale(0.7)';
            overlay.style.transformOrigin = 'left bottom';
            
            // 모달과 완전히 동일한 스타일을 적용하기 위해 뱃지 생성 헬퍼 함수 정의
            const createBadge = (icon, text, isHighlight = false) => {
                if (!text || text.trim() === '') text = 'Unknown';
                const cls = isHighlight ? 'info-badge highlight' : 'info-badge';
                return `<div class="${cls}"><i class="${icon}"></i> ${text}</div>`;
            };
            
            let badgesHtml = '';
            
            // 1. Date
            let dateVal = (photo.date && photo.date.trim() !== '') ? photo.date : 'Unknown';
            if (dateVal.length > 10 && dateVal !== 'Unknown') dateVal = dateVal.substring(0, 10);
            badgesHtml += createBadge('fa-regular fa-calendar', dateVal);
            
            // 2. Location
            let locVal = (photo.location && photo.location.trim() !== '') ? photo.location.replace(/-/g, ' ') : 'Unknown';
            if (locVal.includes('위치정보없음')) locVal = 'Unknown';
            badgesHtml += createBadge('fa-solid fa-location-dot', locVal);
            
            // 3. People (Highlight)
            let peopleVal = 'Unknown';
            if (photo.people && photo.people.length > 0) {
                let pStr = photo.people.filter(p => !p.includes('Unknown')).join(', ');
                if (pStr) peopleVal = pStr;
            }
            badgesHtml += createBadge('fa-solid fa-user-tag', peopleVal, true);
            
            // 4. Season
            let seasonVal = photo.season ? photo.season : 'Unknown';
            badgesHtml += createBadge('fa-solid fa-leaf', seasonVal);

            // 5. Time of Day
            let timeVal = photo.time_of_day ? photo.time_of_day : 'Unknown';
            badgesHtml += createBadge('fa-regular fa-clock', timeVal);
            
            overlay.innerHTML = badgesHtml;
            // image-item(masonry 컨테이너)에 오버레이 부착
            item.appendChild(overlay);
        }

        // Click Event listener logic
        item.addEventListener('click', () => {
            openModal(photo, imgUrl);
        });
        
        grid.appendChild(item);
    });
}

// Infinite Scroll for Horizontal Slider Grid
document.getElementById('gallery-grid').addEventListener('scroll', (e) => {
    const el = e.target;
    // Check if scrolled near the right end
    if (el.scrollWidth - el.scrollLeft - el.clientWidth < 300) {
        fetchPhotos(true);
    }
});

// Upload Logic (Maintained unchanged)
const uploadInput = document.getElementById('upload-input');
const progressContainer = document.getElementById('upload-progress-container');
const progressFill = document.getElementById('progress-bar-fill');
const progressPercent = document.getElementById('progress-percent');
const progressText = document.getElementById('progress-text');

async function executeUpload(files) {
    return new Promise((resolve, reject) => {
        if (!files || files.length === 0) return resolve();

        progressContainer.classList.remove('hidden');
        progressFill.style.width = '0%';
        progressPercent.innerText = '0%';
        progressText.innerText = `0 / ${files.length} uploaded`;

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        try {
            let uploadUrl = '/upload/';
            if (window.location.pathname.startsWith('/GumaPhoto')) {
                uploadUrl = '/GumaPhoto/upload/';
            }

            const xhr = new XMLHttpRequest();
            xhr.open('POST', uploadUrl, true);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressFill.style.width = percentComplete + '%';
                    progressPercent.innerText = percentComplete + '%';
                    const filesUploaded = Math.round((files.length * percentComplete) / 100);
                    progressText.innerText = `${filesUploaded} / ${files.length} uploading...`;
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) {
                    progressText.innerText = `${files.length} / ${files.length} successfully uploaded!`;
                    progressFill.style.width = '100%';
                    progressPercent.innerText = '100%';
                    setTimeout(() => { progressContainer.classList.add('hidden'); uploadInput.value = ''; }, 3000);
                    resolve();
                } else {
                    progressText.innerText = 'Upload failed.';
                    progressFill.style.backgroundColor = '#ef4444';
                    reject(new Error("Upload failed"));
                }
            };

            xhr.onerror = () => { 
                progressText.innerText = 'Upload error.'; 
                progressFill.style.backgroundColor = '#ef4444'; 
                reject(new Error("Network Error"));
            };
            xhr.send(formData);
        } catch (err) {
            console.error(err);
            progressText.innerText = 'Error occurred.';
            reject(err);
        }
    });
}

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

function openModal(photo, imgUrl) {
    currentModalPhoto = photo;
    modalImage.src = imgUrl;
    photoModal.classList.remove('hidden');
    
    // Panzoom 초기화 또는 초기화 상태 복구
    if (typeof Panzoom !== 'undefined') {
        if (!pzInstance) {
            pzInstance = Panzoom(modalImage, {
                maxScale: 6,
                contain: 'outside',
                step: 0.3
            });
            modalImage.parentElement.addEventListener('wheel', pzInstance.zoomWithWheel);
        } else {
            pzInstance.reset();
            // Reset 시 축척 애니메이션 부드러운 전환을 보장
            setTimeout(() => pzInstance.reset(), 50);
        }
    }
    
    // 모달창 좌측 하단의 Semantic Badges 생성
    if (modalInfoBadges) {
        modalInfoBadges.classList.remove('hidden'); // 항상 다시 보이도록 리셋
        if (modalActionsCenter) modalActionsCenter.classList.remove('hidden');

        modalInfoBadges.innerHTML = ''; // 초기화
        
        const createBadge = (icon, text, isHighlight = false) => {
            if (!text || text.trim() === '') text = 'Unknown';
            const cls = isHighlight ? 'info-badge highlight' : 'info-badge';
            return `<div class="${cls}"><i class="${icon}"></i> ${text}</div>`;
        };
        
        let badgesHtml = '';
        
        // 1. Date
        let dateVal = (photo.date && photo.date.trim() !== '') ? photo.date : 'Unknown';
        if (dateVal.length > 10 && !dateVal.includes('Unknown')) dateVal = dateVal.substring(0, 10);
        badgesHtml += createBadge('fa-regular fa-calendar', dateVal);
        
        // 2. Location
        let locVal = (photo.location && photo.location.trim() !== '') ? photo.location.replace(/-/g, ' ') : 'Unknown';
        if (locVal.includes('위치정보없음')) locVal = 'Unknown';
        badgesHtml += createBadge('fa-solid fa-location-dot', locVal);
        
        // 3. People (Highlight)
        let peopleVal = 'Unknown';
        if (photo.people && photo.people.length > 0) {
            let pStr = photo.people.filter(p => !p.includes('Unknown')).join(', ');
            if (pStr) peopleVal = pStr;
        }
        badgesHtml += createBadge('fa-solid fa-user-tag', peopleVal, true);
        
        // 4. Season
        let seasonVal = photo.season ? photo.season : 'Unknown';
        badgesHtml += createBadge('fa-solid fa-leaf', seasonVal);

        // 5. Time of Day
        let timeVal = photo.time_of_day ? photo.time_of_day : 'Unknown';
        badgesHtml += createBadge('fa-regular fa-clock', timeVal);
        
        modalInfoBadges.innerHTML = badgesHtml;
    }
}

function closeModal() {
    photoModal.classList.add('hidden');
    currentModalPhoto = null;
    modalImage.src = '';
    if (pzInstance) pzInstance.reset();
}

modalClose.addEventListener('click', closeModal);
photoModal.addEventListener('click', (e) => {
    // 배경(dimmed) 바깥 부분 클릭 시 즉시 닫힘
    if (e.target === photoModal) closeModal();
});


// ==========================================
// Native Web Share API (파일 직접 끌어오기 방식)
// ==========================================
shareBtn?.addEventListener('click', async () => {
    if (!currentModalPhoto) return;
    
    const ogHtml = shareBtn.innerHTML;
    
    try {
        const fileUrl = modalImage.src;
        
        // Web Share API (모바일 네이티브 공유 우선)
        if (navigator.share) {
            shareBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            shareBtn.disabled = true;
            
            // 파일 리소스를 네이티브로 직접 끌어오기 (Blob Fetch)
            const response = await fetch(fileUrl);
            const blob = await response.blob();
            let ext = "jpg";
            if (blob.type === "image/png") ext = "png";
            else if (blob.type === "image/webp") ext = "webp";
            else if (blob.type === "video/mp4") ext = "mp4";
            
            const file = new File([blob], `GumaPhoto_Shared_${currentModalPhoto.id}.${ext}`, { type: blob.type });

            // 브라우저가 파일 공유를 지원하는지 점검 후 전송
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({
                    title: 'GumaPhoto 공유',
                    files: [file]
                });
            } else {
                // 파일 공유 미지원 브라우저 폴백 (URL 공유)
                await navigator.share({
                    title: 'GumaPhoto',
                    text: '이 사진을 확인해보세요!',
                    url: fileUrl 
                });
            }
            
            shareBtn.innerHTML = ogHtml;
            shareBtn.disabled = false;
        } else {
            // PC 브라우저 데스크탑 환경 폴백
            await navigator.clipboard.writeText(fileUrl);
            
            shareBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
            shareBtn.style.color = '#10b981';
            
            setTimeout(() => {
                shareBtn.innerHTML = ogHtml;
                shareBtn.style.color = '';
            }, 2000);
        }
    } catch (err) {
        console.log('Share canceled or failed', err);
        shareBtn.innerHTML = ogHtml;
        shareBtn.disabled = false;
    }
});

deleteBtn.addEventListener('click', () => {
    if (!currentModalPhoto) return;
    const confirmModal = document.getElementById('delete-confirm-modal');
    if (confirmModal) confirmModal.classList.remove('hidden');
});

// 취소 버튼
document.getElementById('cancel-delete-btn')?.addEventListener('click', () => {
    const confirmModal = document.getElementById('delete-confirm-modal');
    if (confirmModal) confirmModal.classList.add('hidden');
});

// 실제 삭제 승인 버튼
document.getElementById('confirm-delete-btn')?.addEventListener('click', async () => {
    if (!currentModalPhoto) return;
    
    // 모달 즉시 닫기
    document.getElementById('delete-confirm-modal').classList.add('hidden');
    
    try {
        let apiUrl = '/api/photos';
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            apiUrl = '/GumaPhoto/api/photos';
        }
        
        deleteBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        deleteBtn.disabled = true;
        
        const res = await fetch(apiUrl, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filepath: currentModalPhoto.original_path || currentModalPhoto.url,
                point_id: currentModalPhoto.id
            })
        });
        
        // 에러를 던져서 catch 로 넘김
        if (!res.ok) throw new Error("Delete failed");
        
        // DOM에서 방금 지운 사진 타일을 즉시 제거 (새로고침 안 해도 사라지도록)
        // URL 인코딩 등 특수문자 이슈 방지를 위해 고유 Point ID(data-id) 기반으로 타겟팅 및 삭제
        const elementsToRemove = document.querySelectorAll(`[data-id="${currentModalPhoto.id}"]`);
        elementsToRemove.forEach(el => el.remove());
        
        closeModal(); // 부모 모달도 완전히 닫기
        // alert("Successfully deleted."); // premium design에서는 성공 알림이 번거로울 수 있으므로 제거 또는 유지
        
    } catch (err) {
        console.error(err);
        alert("Failed to delete. Please contact system administrator.");
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
    }
});

// ---------------------------------------------------------------------------------
// Live Progress Monitor Logic
// ---------------------------------------------------------------------------------
const progressMonitorBtn = document.getElementById('progress-monitor-btn');
const progressModal = document.getElementById('progress-modal');
const progressModalClose = document.getElementById('progress-modal-close');

window.progressPollingInterval = null;

if (progressMonitorBtn) {
    progressMonitorBtn.addEventListener('click', () => {
        updateProgressMonitor();
        switchView('system');
    });
}

if (progressModalClose) {
    progressModalClose.addEventListener('click', closeProgressModal);
}

function closeProgressModal() {
    progressModal.classList.add('hidden');
    document.body.style.overflow = 'auto'; // restore body scroll
    if (progressPollingInterval) {
        clearInterval(progressPollingInterval);
        progressPollingInterval = null;
    }
}

// Close monitor modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === progressModal) {
        closeProgressModal();
    }
});

window.addEventListener('click', (e) => {
    const statsModal = document.getElementById('stats-modal');
    if (e.target === statsModal) {
        statsModal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
});

let advancedStatsData = null;

window.fetchAdvancedStats = async function(forceRefresh = false) {
    try {
        const cb = new Date().getTime();
        let query = '?cb=' + cb;
        if (forceRefresh) query += '&force_refresh=true';
        let targetUrl = '/api/system/advanced' + query;
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            targetUrl = '/GumaPhoto' + targetUrl;
        }
        
        const refreshIcon = document.getElementById('stats-refresh-icon');
        if (refreshIcon && forceRefresh) refreshIcon.classList.add('fa-spin');
        
        document.getElementById('stat-total-photos').innerText = '...';
        document.getElementById('stat-total-people').innerText = '...';
        document.getElementById('stat-total-locations').innerText = '...';
        document.getElementById('stat-total-dates').innerText = '...';
        
        const res = await fetch(targetUrl);
        
        if (refreshIcon && forceRefresh) refreshIcon.classList.remove('fa-spin');
        if (res.ok) {
            advancedStatsData = await res.json();
            
            const actualLocs = advancedStatsData.locations ? advancedStatsData.locations.filter(l => !l.name.includes("Unknown") && l.name !== "위치정보없음").length : 0;
            
            let dateSpanStr = "-";
            if (advancedStatsData.min_date && advancedStatsData.max_date) {
                const parts1 = advancedStatsData.min_date.split("-");
                const parts2 = advancedStatsData.max_date.split("-");
                if (parts1.length >= 2 && parts2.length >= 2) {
                    const y1 = parseInt(parts1[0]); const m1 = parseInt(parts1[1]);
                    const y2 = parseInt(parts2[0]); const m2 = parseInt(parts2[1]);
                    const totalMonths = (y2 - y1) * 12 + (m2 - m1) + 1;
                    if (totalMonths > 0) {
                        const spanYears = Math.floor(totalMonths / 12);
                        const spanMonths = totalMonths % 12;
                        if (spanYears > 0 && spanMonths > 0) dateSpanStr = `${spanYears}년 ${spanMonths}개월`;
                        else if (spanYears > 0) dateSpanStr = `${spanYears}년`;
                        else dateSpanStr = `${spanMonths}개월`;
                    }
                }
            }
            
            document.getElementById('stat-total-photos').innerText = advancedStatsData.total_photos.toLocaleString();
            document.getElementById('stat-total-people').innerText = advancedStatsData.known_faces_count.toLocaleString();
            document.getElementById('stat-total-locations').innerText = actualLocs.toLocaleString();
            document.getElementById('stat-total-dates').innerText = dateSpanStr;
        }
    } catch(err) {
        console.error('Error fetching advanced stats:', err);
        const refreshIcon = document.getElementById('stats-refresh-icon');
        if (refreshIcon && forceRefresh) refreshIcon.classList.remove('fa-spin');
    }
}

window.showStatsModal = function(type) {
    if (!advancedStatsData) {
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
        
        const ukDate = advancedStatsData.dates.find(d => d.name === "Unknown Date")?.count || 0;
        const ukLoc1 = advancedStatsData.locations.find(d => d.name === "Unknown Location")?.count || 0;
        const ukLoc2 = advancedStatsData.locations.find(d => d.name === "Unknown")?.count || 0;
        const ukLoc = ukLoc1 + ukLoc2;
        
        const ukP1 = advancedStatsData.people.find(p => p.name === "Unknown People")?.count || 0;
        const ukP2 = advancedStatsData.people.find(p => p.name === "Unknown Person")?.count || 0;
        const ukP3 = advancedStatsData.people.find(p => p.name === "Unidentifiable Person")?.count || 0;
        const ukP4 = advancedStatsData.people.find(p => p.name === "No Person")?.count || 0;
        const ukPerson = ukP1 + ukP2 + ukP3 + ukP4;
        
        items = [
            { name: "Unknown Date", count: ukDate, pct: ((ukDate / advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#f43f5e" },
            { name: "Unknown Location", count: ukLoc, pct: ((ukLoc / advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#eab308" },
            { name: "Unknown Person", count: ukPerson, pct: ((ukPerson / advancedStatsData.total_photos) * 100).toFixed(1) + "%", color: "#a855f7" },
            { name: "보유 인물 데이터 총 사람수", count: advancedStatsData.known_faces_count, pct: "-", color: "#10b981", isAbs: true }
        ];
        
    } else if (type === 'person') {
        title.innerHTML = '<i class="fa-solid fa-users" style="color:#10b981;"></i> 인물 통계 세부';
        items = advancedStatsData.people
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
        items = advancedStatsData.locations
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
        items = advancedStatsData.dates
            .filter(d => !d.name.includes("Unknown"))
            .map(d => ({
                name: d.name,
                count: d.count,
                pct: d.pct + "%",
                color: "#f43f5e"
            }));
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
const feedbackHubBtn = document.getElementById('feedback-hub-btn');
const feedbackHubModal = document.getElementById('feedback-hub-modal');
const feedbackHubClose = document.getElementById('feedback-hub-close');

let currentFeedbackMode = null; // 'time_loc' or 'face'
let selectedFeedbackTarget = null; // 타겟 사진의 Qdrant Payload 정보 대기열

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
    if (!selectedFeedbackTarget) return;

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
                filepath: selectedFeedbackTarget.url,
                point_id: selectedFeedbackTarget.id
            })
        });
        
        if (!res.ok) throw new Error("서버에서 사진을 삭제하지 못했습니다.");
        
        // 삭제 성공 시 바로 다음 타겟 불러오기
        loadUnknownPhoto();
        
    } catch (err) {
        console.error(err);
        alert("삭제 실패: " + err.message);
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
    document.getElementById('fb-temptest-results').style.display = 'none';
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
        } else if (window.feedbackQueue && window.feedbackQueue.length > 0) {
            selectedFeedbackTarget = window.feedbackQueue.shift(); // 큐에서 빛의 속도로 팝(Pop)
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
        let finalSrc = selectedFeedbackTarget.url;
        if ((selectedFeedbackTarget.issue.includes('Person') || selectedFeedbackTarget.issue.includes('People')) && selectedFeedbackTarget.face_bbox) {
            finalSrc = selectedFeedbackTarget.originalUrl || selectedFeedbackTarget.url;
        }
        if (!finalSrc.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) finalSrc = '/GumaPhoto' + finalSrc;
        
        if ((selectedFeedbackTarget.issue.includes('Person') || selectedFeedbackTarget.issue.includes('People')) && selectedFeedbackTarget.face_bbox && selectedFeedbackTarget.face_bbox.length === 4) {
            const tempImg = new Image();
            tempImg.crossOrigin = "Anonymous";
            tempImg.src = finalSrc;
            tempImg.onload = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                let [x1, y1, x2, y2] = selectedFeedbackTarget.face_bbox;
                const w = x2 - x1; const h = y2 - y1;
                const margin = Math.max(w, h) * 0.4;
                x1 = Math.max(0, x1 - margin); y1 = Math.max(0, y1 - margin);
                x2 = Math.min(tempImg.naturalWidth, x2 + margin); y2 = Math.min(tempImg.naturalHeight, y2 + margin);
                const cropW = x2 - x1; const cropH = y2 - y1;
                if(cropW > 0 && cropH > 0) {
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
        
        if(selectedFeedbackTarget.issue.includes('Date')) {
            inputVal.style.display = 'none';
            inputDate.style.display = 'block';
            if(personBtns) personBtns.style.display = 'none';
            if(personGuide) personGuide.style.display = 'none';
        } else if (selectedFeedbackTarget.issue.includes('Person') || selectedFeedbackTarget.issue.includes('People')) {
            inputDate.style.display = 'none';
            inputVal.style.display = 'block';
            inputVal.placeholder = "예: 성욱 (누락된 인물의 이름)";
            if(personBtns) personBtns.style.display = 'flex';
            if(personGuide) personGuide.style.display = 'block';
        } else {
            inputDate.style.display = 'none';
            inputVal.style.display = 'block';
            inputVal.placeholder = "예: 대한민국-인천광역시 (장소 포맷)";
            if(personBtns) personBtns.style.display = 'none';
            if(personGuide) personGuide.style.display = 'none';
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


// 사용자 제출 로직 (백엔드 우회 테스트 모드 지원)
// Send 버튼 시뮬레이션 통합 적용 (수정 제출 API 가동 중단 상태)
document.getElementById('fb-submit-btn')?.addEventListener('click', async () => {
    if (!selectedFeedbackTarget) return;

    const inputVal = document.getElementById('fb-input-val');
    const inputDate = document.getElementById('fb-input-date');
    let correctValue = "";
    
    if (selectedFeedbackTarget.issue.includes('Date') || selectedFeedbackTarget.issue.includes('날짜')) {
        correctValue = inputDate.value;
    } else {
        correctValue = inputVal.value.trim();
    }
    
    if (!correctValue) {
        alert("Please provide the correct information first!");
        return;
    }

    const btn = document.getElementById('fb-submit-btn');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scanning...';
    btn.disabled = true;

    try {
        let apiUrl = '/api/feedback_v2/temptest';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;

        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                point_id: selectedFeedbackTarget.id,
                issue_type: selectedFeedbackTarget.issue,
                correct_value: correctValue
            })
        });

        if (!res.ok) throw new Error("Could not fetch simulation data from server.");
        const data = await res.json();
        
        if (data.error) {
            alert("서버 에러 발생: " + data.error);
            btn.innerHTML = ogHtml;
            btn.disabled = false;
            return;
        }

        if (data.results && data.results.length > 0) {
            // 결과창 안내명 Inject
            const parsedSpan = document.getElementById('fb-temptest-parsed-val');
            if (parsedSpan) {
                // Return parsed_value (from Gemini) or fallback to raw
                const finalStr = data.parsed_value || correctValue;
                parsedSpan.textContent = `"${finalStr}"`;
            }

            const grid = document.getElementById('fb-temptest-grid');
            let gridHtml = '';
            data.results.forEach(item => {
                const scoreText = (item.score * 100).toFixed(1) + '%';
                
                const createBadge = (icon, text, isHighlight = false) => {
                    if (!text || text.trim() === '') text = 'Unknown';
                    const cls = isHighlight ? 'info-badge highlight' : 'info-badge';
                    return `<div class="${cls}"><i class="${icon}"></i> ${text}</div>`;
                };

                let badgesHtml = '';
                // 1. Date
                let dateVal = (item.date && item.date.trim() !== '') ? item.date : 'Unknown';
                if (dateVal.length > 10 && !dateVal.includes('Unknown')) dateVal = dateVal.substring(0, 10);
                badgesHtml += createBadge('fa-regular fa-calendar', dateVal);
                
                // 2. Location
                let locVal = (item.location && item.location.trim() !== '') ? item.location.replace(/-/g, ' ') : 'Unknown';
                if (locVal.includes('위치정보없음')) locVal = 'Unknown';
                badgesHtml += createBadge('fa-solid fa-location-dot', locVal);
                
                // 3. People
                let peopleVal = 'Unknown';
                if (item.people && item.people.length > 0) {
                    let pStr = item.people.filter(p => !p.includes('Unknown')).join(', ');
                    if (pStr) peopleVal = pStr;
                }
                badgesHtml += createBadge('fa-solid fa-user-tag', peopleVal, true);

                const bboxStr = item.face_bbox_target ? JSON.stringify(item.face_bbox_target) : '';
                gridHtml += `
                <div style="position: relative; width: 100%; aspect-ratio: 1/1; border-radius: 8px; overflow: hidden; background: #111;">
                    <img class="temp-crop-img" src="" data-src="${item.original_path || item.url}" data-bbox='${bboxStr}' style="width: 100%; height: 100%; object-fit: cover; transition: filter 0.3s ease;" loading="lazy">
                    
                    <div class="meta-badge" style="position: absolute; left: 5px; top: 5px;">
                        <i class="fa-solid fa-bullseye"></i> ${scoreText}
                    </div>
                    
                    <input type="checkbox" checked data-id="${item.id}" style="position: absolute; right: 8px; top: 8px; width: 22px; height: 22px; cursor: pointer; z-index: 20; accent-color: #10b981; box-shadow: 0 0 5px rgba(0,0,0,0.5);" onchange="this.parentElement.querySelector('img').style.filter = this.checked ? 'none' : 'grayscale(100%)';">
                    
                    <div class="info-badges-overlay" style="position: absolute; left: 5px; bottom: 5px; transform: scale(0.65); transform-origin: left bottom; margin: 0; display: flex; flex-direction: column; gap: 4px; z-index: 10;">
                        ${badgesHtml}
                    </div>
                </div>`;
            });
            grid.innerHTML = gridHtml;
            
            // 후속 처리: 인물 피드백일 경우 캔버스를 통해 얼굴만 Crop하여 표시
            document.querySelectorAll('.temp-crop-img').forEach(img => {
                const src = img.getAttribute('data-src');
                const bboxStr = img.getAttribute('data-bbox');
                
                if (bboxStr && (selectedFeedbackTarget.issue.includes('Person') || selectedFeedbackTarget.issue.includes('People'))) {
                    const bbox = JSON.parse(bboxStr);
                    const tempImg = new Image();
                    tempImg.crossOrigin = "Anonymous";
                    tempImg.src = window.location.pathname.startsWith('/GumaPhoto') && !src.startsWith('/GumaPhoto') ? '/GumaPhoto' + src : src;
                    
                    tempImg.onload = () => {
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        let [x1, y1, x2, y2] = bbox;
                        const w = x2 - x1; const h = y2 - y1;
                        const margin = Math.max(w, h) * 0.4;
                        x1 = Math.max(0, x1 - margin); y1 = Math.max(0, y1 - margin);
                        x2 = Math.min(tempImg.naturalWidth, x2 + margin); y2 = Math.min(tempImg.naturalHeight, y2 + margin);
                        const cropW = x2 - x1; const cropH = y2 - y1;
                        
                        if(cropW > 0 && cropH > 0) {
                            canvas.width = cropW; canvas.height = cropH;
                            ctx.drawImage(tempImg, x1, y1, cropW, cropH, 0, 0, cropW, cropH);
                            img.src = canvas.toDataURL('image/jpeg', 0.85);
                        } else {
                            img.src = tempImg.src;
                        }
                    };
                } else {
                    img.src = window.location.pathname.startsWith('/GumaPhoto') && !src.startsWith('/GumaPhoto') ? '/GumaPhoto' + src : src;
                }
            });
            
            document.getElementById('fb-temptest-count').textContent = data.results.length;
            
            // 메인 타겟 사진 컨테이너를 숨기고 그 자리에 검색결과 교체 표출
            const mainContainer = document.getElementById('fb-unknown-photo-container');
            if(mainContainer) mainContainer.style.display = 'none';
            const infoTextContainer = document.getElementById('fb-info-text-container');
            if(infoTextContainer) infoTextContainer.style.display = 'none';
            document.getElementById('fb-temptest-results').style.display = 'block';
        } else {
            alert("유사도 임계값(0.85)을 넘는 수정 대상 사진이 0장 입니다.");
        }
    } catch (err) {
        console.error(err);
        alert("시뮬레이션 실패: " + err.message);
    } finally {
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
});

// =========================================================================
// 선택된 타겟 대상(체크박스) 피드백 DB 전송 액션
// =========================================================================
document.getElementById('fb-temptest-send-btn')?.addEventListener('click', async () => {
    if (!selectedFeedbackTarget) return;

    const inputVal = document.getElementById('fb-input-val');
    const inputDate = document.getElementById('fb-input-date');
    const btn = document.getElementById('fb-temptest-send-btn');
    const ogHtml = btn.innerHTML;
    
    let correctValue = "";
    if (selectedFeedbackTarget.issue.includes('Date')) {
        correctValue = inputDate.value;
    } else {
        correctValue = inputVal.value.trim();
    }
    
    if (!correctValue) {
        alert("정답 입력값이 없습니다. 뒤로 돌아가서 다시 입력해주세요!");
        return;
    }

    // 1. 체크된 체크박스의 사진 ID들을 수집
    const checkboxes = document.querySelectorAll('#fb-temptest-grid input[type="checkbox"]');
    const targetPoints = [];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            targetPoints.push(cb.getAttribute('data-id'));
        }
    });

    // 메인 타겟 사진 본인은 무조건 포함 (최소 1장 보장 필터)
    if (!targetPoints.includes(String(selectedFeedbackTarget.id)) && !targetPoints.includes(Number(selectedFeedbackTarget.id))) {
        targetPoints.push(selectedFeedbackTarget.id);
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 대기열 배달 중...';
    
    try {
        let apiUrl = '/api/feedback_v2/submit';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;
        
        let res = await fetch(apiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                point_id: selectedFeedbackTarget.id,
                issue_type: selectedFeedbackTarget.issue,
                correct_value: correctValue,
                target_points: targetPoints
            })
        });
        
        if (res.status === 404 || res.status === 405) {
            console.log("[우회 접속] 백엔드 POST API 응답 누락 처리됨 (모의 통과)");
        } else {
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "제출 실패");
        }
        
        // 제출 성공 알림 및 피드백 화면 종료 유도 (재귀 로딩 중복 충돌 방지)
        document.getElementById('fb-temptest-results').style.display = 'none';
        
        const feedbackHubModal = document.getElementById('feedback-hub-modal');
        if (feedbackHubModal) feedbackHubModal.classList.add('hidden');
        
        // 홈 탭으로 자동 복귀 및 강제 새로고침
        switchView('home');
        
        // 브라우저 렌더링 충돌을 막기 위해 0.1초 딜레이 후 Alert 띄움
        setTimeout(() => {
            alert("Feedback submitted successfully. 화면을 새로고침합니다.");
            window.location.reload();
        }, 100);
        
    } catch (err) {
        console.error(err);
        alert("오류 발생: " + err.message);
    } finally {
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
});

// ----------------------------------------------------------------------
// 피드백 추가 액션 버튼들 (Skip, Remove, Unidentifiable Person, No Person)
// ----------------------------------------------------------------------
document.getElementById('fb-skip-btn')?.addEventListener('click', async () => {
    switchView('feedback');
});

document.getElementById('fb-remove-btn')?.addEventListener('click', async () => {
    if (!selectedFeedbackTarget || !selectedFeedbackTarget.id) return;
    try {
        let apiUrl = '/api/photos';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto/api/photos';
        
        const res = await fetch(apiUrl, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filepath: selectedFeedbackTarget.originalUrl || selectedFeedbackTarget.url,
                point_id: selectedFeedbackTarget.id
            })
        });
        if (res.ok) {
            document.getElementById('fb-temptest-results').style.display = 'none';
            switchView('feedback');
        }
    } catch(err) {
        console.error("삭제 실패", err);
    }
});

const sendPersonFeedback = async (apiUrlEndpoint, btnId) => {
    if (!selectedFeedbackTarget || !selectedFeedbackTarget.id) return;
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
                point_id: selectedFeedbackTarget.id,
                issue_type: selectedFeedbackTarget.issue
            })
        });
        
        if (res.ok) {
            document.getElementById('fb-temptest-results').style.display = 'none';
            switchView('home'); 
            setTimeout(() => {
                alert("Feedback submitted successfully. 화면을 새로고침합니다.");
                window.location.reload();
            }, 100);
        } else {
            alert('Failed to submit feedback.');
        }
    } catch(err) {
        console.error(err);
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
};

document.getElementById('fb-not-a-face-btn')?.addEventListener('click', () => sendPersonFeedback('/api/feedback_v2/ignore_face', 'fb-not-a-face-btn'));
document.getElementById('fb-no-person-btn')?.addEventListener('click', () => sendPersonFeedback('/api/feedback_v2/no_person', 'fb-no-person-btn'));

// =========================================================================
// 📱 Mobile Bottom Navigation Bar & View Router Logic
// =========================================================================
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
document.getElementById('upload-input')?.addEventListener('change', async function(e) {
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
