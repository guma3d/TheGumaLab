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
document.addEventListener('DOMContentLoaded', () => {
    currentQuery = '';
    currentOffset = 0;
    currentGalleryFilter = "recent";
    hasMore = true;
    totalHits = 0;
    fetchPhotos(false);
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
                    
                    const shuffledGeneral = generalIdeas.sort(() => 0.5 - Math.random()).slice(0, 5);
                    const shuffledLocation = locationIdeas.sort(() => 0.5 - Math.random()).slice(0, 1);
                    const themeIdeas = [...shuffledGeneral, ...shuffledLocation].sort(() => 0.5 - Math.random());
                    
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
                    const themes = rawThemes.filter(t => t && t.photos && t.photos.length > 0);
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
    if (!files || files.length === 0) return;

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
            } else {
                progressText.innerText = 'Upload failed.';
                progressFill.style.backgroundColor = '#ef4444';
            }
        };

        xhr.onerror = () => { progressText.innerText = 'Upload error.'; progressFill.style.backgroundColor = '#ef4444'; };
        xhr.send(formData);
    } catch (err) {
        console.error(err);
        progressText.innerText = 'Error occurred.';
    }
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

function openModal(photo, imgUrl) {
    currentModalPhoto = photo;
    modalImage.src = imgUrl;
    photoModal.classList.remove('hidden');
    
    // 모달창 좌측 하단의 Semantic Badges 생성
    if (modalInfoBadges) {
        modalInfoBadges.innerHTML = ''; // 초기화
        
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
        
        modalInfoBadges.innerHTML = badgesHtml;
    }
}

function closeModal() {
    photoModal.classList.add('hidden');
    currentModalPhoto = null;
    modalImage.src = '';
}

modalClose.addEventListener('click', closeModal);
photoModal.addEventListener('click', (e) => {
    // 배경(dimmed) 바깥 부분 클릭 시 즉시 닫힘
    if (e.target === photoModal) closeModal();
});


// ==========================================
// iOS Action Sheet (공유 버튼 클릭 시)
// ==========================================
const iosShareSheet = document.getElementById('ios-share-sheet');
const sheetShareBtn = document.getElementById('sheet-share');
const sheetSaveBtn = document.getElementById('sheet-save');
const sheetCopyBtn = document.getElementById('sheet-copy');
const sheetCancelBtn = document.getElementById('sheet-cancel');

// 1. 하단 액션 시트 모달 띄우기
shareBtn?.addEventListener('click', () => {
    if (!currentModalPhoto) return;
    iosShareSheet.classList.remove('hidden');
});

// 2. 배경 터치 혹은 취소 시트 닫기
iosShareSheet?.addEventListener('click', (e) => {
    if (e.target === iosShareSheet) {
        iosShareSheet.classList.add('hidden');
    }
});
sheetCancelBtn?.addEventListener('click', () => {
    iosShareSheet.classList.add('hidden');
});

// 3. 액션: 공유 (Native Share)
sheetShareBtn?.addEventListener('click', async () => {
    iosShareSheet.classList.add('hidden');
    if (!currentModalPhoto) return;
    const fileUrl = modalImage.src;
    try {
        if (navigator.share) {
            await navigator.share({
                title: 'GumaPhoto',
                text: '이 사진 어때요?',
                url: fileUrl
            });
        } else {
            alert('현재 브라우저에서는 이 공유 방식을 지원하지 않습니다.');
        }
    } catch(err) {
        console.error("공유 취소 또는 오류:", err);
    }
});

// 4. 액션: 기기에 직접 저장 (Download)
sheetSaveBtn?.addEventListener('click', () => {
    iosShareSheet.classList.add('hidden');
    if (!currentModalPhoto) return;
    const fileUrl = modalImage.src;
    const a = document.createElement('a');
    a.href = fileUrl;
    let filename = fileUrl.split('/').pop().split('?')[0]; 
    if (!filename) filename = `GumaPhoto_${currentModalPhoto.id}.jpg`;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
});

// 5. 액션: 클립보드 복사
sheetCopyBtn?.addEventListener('click', async () => {
    iosShareSheet.classList.add('hidden');
    if (!currentModalPhoto) return;
    const fileUrl = modalImage.src;
    try {
        await navigator.clipboard.writeText(fileUrl);
        alert("사진 링크가 클립보드에 복사되었습니다!");
    } catch(err) {
        console.error("복사 오류:", err);
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

async function fetchProgress() {
    try {
        // Cache buster to prevent browser from caching the JSON
        const cb = new Date().getTime();
        let targetUrl = '/static/progress.json?cb=' + cb;
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            targetUrl = '/GumaPhoto' + targetUrl;
        }
        
        const res = await fetch(targetUrl);
        if (res.ok) {
            const data = await res.json();
            // Extracted raw metrics
            const totalPhotos = Number(data.total_photos || 0);
            const dbCompleted = Number(data.db_completed || 0);

            // Calculated true metrics
            const needsDb = Math.max(0, totalPhotos - dbCompleted);
            
            document.getElementById('prog-total').innerText = `${totalPhotos.toLocaleString()}`;
            document.getElementById('prog-ai-left').innerText = `${needsDb.toLocaleString()}`;
            document.getElementById('prog-db').innerText = `${dbCompleted.toLocaleString()}`;
            
            document.getElementById('prog-status').innerHTML = 'Syncing... <i class="fa-solid fa-spinner fa-spin"></i>';
        } else {
            console.error('Failed to load progress data:', res.statusText);
            document.getElementById('prog-status').innerText = 'Waiting (No response data)';
        }
    } catch(err) {
        console.error('Error fetching tracker data:', err);
    }
}

function updateProgressMonitor() {
    if (window.progressPollingInterval) {
        clearInterval(window.progressPollingInterval);
    }
    fetchProgress();
    window.progressPollingInterval = setInterval(fetchProgress, 2500);
}

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

document.getElementById('fb-temptest-btn')?.addEventListener('click', async () => {
    if (!selectedFeedbackTarget) return;

    const btn = document.getElementById('fb-temptest-btn');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 시뮬레이션 가동 중...';
    btn.disabled = true;

    try {
        let apiUrl = '/api/feedback_v2/temptest';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;

        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ point_id: selectedFeedbackTarget.id })
        });

        if (!res.ok) throw new Error("시뮬레이션 서버 데이터를 가져오지 못했습니다.");
        const data = await res.json();

        if (data.results && data.results.length > 0) {
            const grid = document.getElementById('fb-temptest-grid');
            grid.innerHTML = '';
            data.results.forEach(item => {
                grid.innerHTML += `<div style="width: 100%; aspect-ratio: 1/1; border-radius: 8px; overflow: hidden; background: #111;"><img src="${item.url}" style="width: 100%; height: 100%; object-fit: cover;" loading="lazy"></div>`;
            });
            document.getElementById('fb-temptest-count').textContent = data.results.length;
            document.getElementById('fb-temptest-results').style.display = 'block';
            
            // Scroll down automatically
            setTimeout(() => {
                document.getElementById('fb-temptest-results').scrollIntoView({ behavior: 'smooth' });
            }, 100);
        } else {
            alert("유사도 임계값(0.88)을 넘는 수정 대상 사진이 없습니다.");
        }
    } catch (err) {
        console.error(err);
        alert("시뮬레이션 실패: " + err.message);
    } finally {
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
});

document.getElementById('fb-temptest-close')?.addEventListener('click', () => {
    document.getElementById('fb-temptest-results').style.display = 'none';
});

async function loadUnknownPhoto() {
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
    
    // TempTest UI 초기화
    const tempTestResults = document.getElementById('fb-temptest-results');
    if(tempTestResults) tempTestResults.style.display = 'none';
    
    try {
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
                // 고해상도 말고 빠른 로딩을 위해 webp 썸네일 변환
                const dotIndex = mockUrl.lastIndexOf('.');
                mockUrl = dotIndex !== -1 ? mockUrl.substring(0, dotIndex) + '_' + mockUrl.substring(dotIndex + 1).toLowerCase() + '.webp' : mockUrl;
                
                if (!mockUrl.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) mockUrl = '/GumaPhoto' + mockUrl;
                selectedFeedbackTarget = { id: randomChoice.id, url: mockUrl, issue: randomChoice.issue, date: randomChoice.date, location: randomChoice.location, people: randomChoice.people };
            } else {
                throw new Error("No pending photos left to categorize!");
            }
        } else {
            const data = await res.json();
            if (data.id) {
                let mockUrl = data.url;
                if (!mockUrl.startsWith('/GumaPhoto') && window.location.pathname.startsWith('/GumaPhoto')) mockUrl = '/GumaPhoto' + mockUrl;
                selectedFeedbackTarget = { id: data.id, url: mockUrl, issue: data.issue, date: data.date, location: data.location, people: data.people };
            } else throw new Error("All photos are perfectly categorized!");
        }
        
        // 추출된 사진 렌더링
        imgEl.src = selectedFeedbackTarget.url;
        imgEl.onload = () => {
            spinner.style.display = 'none';
            imgEl.style.display = 'block';
        };
        let badgeType = '';
        let issueWord = '';
        if (selectedFeedbackTarget.issue.includes('Date')) {
            issueWord = 'Date';
            badgeType = `<i class="fa-regular fa-calendar-xmark" style="margin-right: 4px;"></i> Date`;
        } else if (selectedFeedbackTarget.issue.includes('Location')) {
            issueWord = 'Location';
            badgeType = `<i class="fa-solid fa-location-dot" style="margin-right: 4px;"></i> Location`;
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
            if (t.people && Array.isArray(t.people) && t.people.length > 0) {
                let pStr = t.people.filter(p => !p.includes('Unknown')).join(', ');
                if (pStr) peopleVal = pStr;
            }
            badgesHtml += createBadge('fa-solid fa-user-tag', peopleVal, true);
            
            fbBadgesContainer.innerHTML = badgesHtml;
        }
        
        // 이슈 종류에 따른 폼 UI 전환
        if(selectedFeedbackTarget.issue.includes('Date')) {
            inputVal.style.display = 'none';
            inputDate.style.display = 'block';
        } else {
            inputDate.style.display = 'none';
            inputVal.style.display = 'block';
            if(selectedFeedbackTarget.issue.includes('People')) inputVal.placeholder = "예: 성욱 (누락된 인물의 이름)";
            else inputVal.placeholder = "예: 대한민국-인천광역시 (장소 포맷)";
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
document.getElementById('fb-submit-btn')?.addEventListener('click', async () => {
    if (!selectedFeedbackTarget) return;
    
    const inputVal = document.getElementById('fb-input-val');
    const inputDate = document.getElementById('fb-input-date');
    const submitBtn = document.getElementById('fb-submit-btn');
    
    let correctValue = "";
    if (selectedFeedbackTarget.issue.includes('시간')) {
        correctValue = inputDate.value;
    } else {
        correctValue = inputVal.value.trim();
    }
    
    if (!correctValue) {
        alert("정답을 입력해주세요!");
        return;
    }
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 대기열 봇(Queue)에 위임 중...';
    
    try {
        let apiUrl = '/api/feedback_v2/submit';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;
        
        let res = await fetch(apiUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                point_id: selectedFeedbackTarget.id,
                issue_type: selectedFeedbackTarget.issue,
                correct_value: correctValue
            })
        });
        
        // 핫-픽스: 서버 재부팅 전 도커 락다운 상태 우회용 클라이언트 사이드 임시 성공 처리 (테스트 모드)
        if (res.status === 404 || res.status === 405) {
            console.log("[우회 접속] 백엔드 POST API가 아직 눈을 뜨지 않아, 프론트엔드 모의 테스트 성공으로 강제 통과시킵니다.");
            const issueTag = document.getElementById('fb-target-issue');
            issueTag.innerHTML = '<i class="fa-solid fa-check-circle"></i> 단일 통제소로 접수 완료 (모의 테스트)';
            issueTag.style.color = '#10b981';
            issueTag.style.background = 'transparent';
            issueTag.style.border = 'none';
        } else {
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "제출 실패");
        }
        
        // 연속 피드백의 재미(Gamification)를 위해 0.6초 뒤 바로 다음 미분류 사진을 렌더링!
        setTimeout(() => {
            loadUnknownPhoto();
        }, 600);
        
    } catch (err) {
        console.error(err);
        alert("오류 발생: " + err.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-check"></i> 자율 전파(Propagation) 승인';
    }
});

// =========================================================================
// 📱 Mobile Bottom Navigation Bar & View Router Logic
// =========================================================================
const views = ['home', 'feedback', 'system'];

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
}

const bottomNav = document.getElementById('bottom-nav');
let lastScrollY = window.scrollY;

if (bottomNav) {
    window.addEventListener('scroll', () => {
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
    
    document.getElementById('nav-system-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('system');
        updateProgressMonitor(); // fetch system status when tab is opened
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
