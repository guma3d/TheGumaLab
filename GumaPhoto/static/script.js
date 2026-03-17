let currentQuery = '';
let currentGalleryFilter = "recent";
let currentOffset = 0;
let currentLimit = 20;
let currentPeople = [];
let currentLocation = '';
let currentScene = '';
let isFetching = false;
let hasMore = true;
let totalHits = 0;

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
        
        // Reset and load tag timeline or random home
        currentQuery = '';
        currentOffset = 0;
        hasMore = true;
        totalHits = 0;
        document.getElementById('gallery-grid').innerHTML = '';
        fetchPhotos(false);
    }
});

// Search Form Handler
document.getElementById('search-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const query = document.getElementById('search-query').value.trim();
    
    currentQuery = query; // allow empty to go back to home timeline
    currentOffset = 0;
    hasMore = true;
    totalHits = 0;
    document.getElementById('gallery-grid').innerHTML = '';

    await fetchPhotos(false);
});

async function fetchPhotos(isLoadMore) {
    if (isFetching || !hasMore) return;
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
            metaContainer.classList.add('hidden');
            
            if (!isLoadMore) {
                // Determine if we want themes
                let fetchThemes = (themesContainer.innerHTML === '');
                
                let themePromises = [];
                if (fetchThemes) {
                    const allThemeIdeas = [
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
                    const shuffled = allThemeIdeas.sort(() => 0.5 - Math.random());
                    const themeIdeas = shuffled.slice(0, 3);
                    
                    themePromises = themeIdeas.map(t => fetch(apiUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            query: "theme_dummy", offset: 0, limit: 12, is_load_more: true,
                            people: [], location: "", scene: t.scene
                        })
                    }).then(r => r.json()).then(data => ({
                        title: t.title,
                        photos: data.results || []
                    })));
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
                    body: JSON.stringify({
                        query: t_query, offset: currentOffset, limit: t_limit, is_load_more: true,
                        people: t_people, location: "", scene: t_scene
                    })
                }).then(r => r.json());

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
                
                renderGallery(results, false);
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
                renderGallery(results, true);
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
                themesContainer.classList.add('hidden');
                timelineHeader.classList.add('hidden');
                
                let fallbackMsg = '';
                if (data.fallback_triggered && !isLoadMore) {
                    fallbackMsg = `<br><span style="color:#ef4444; font-size: 0.9em; margin-top:5px; display:inline-block;">⚠️ No exact match for '${currentLocation}', showing photos with similar atmosphere instead.</span>`;
                }
    
                metaText.innerHTML = `Loaded <b style="color:white">${totalHits}</b> photos for: "<i style="color:var(--text-muted)">${currentQuery}</i>" <br> 
                <small style="color:#3b82f6;">(AI concept: ${currentScene})</small>${fallbackMsg}`;
                metaContainer.classList.remove('hidden');
                
                renderGallery(data.results, isLoadMore);
            }
        }
        
    } catch (err) {
        console.error(err);
        metaText.innerHTML = 'An expected error occurred while fetching photos.';
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
            
            let imgUrl = photo.url;
            if (window.location.pathname.startsWith('/GumaPhoto')) {
                imgUrl = '/GumaPhoto' + imgUrl;
            }
            
            const img = document.createElement('img');
            img.src = imgUrl;
            img.loading = "lazy";
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
function renderGallery(photos, append = false) {
    const grid = document.getElementById('gallery-grid');
    if (!append) grid.innerHTML = '';

    if (photos.length === 0 && !append) {
        grid.innerHTML = '<p style="color: var(--text-muted);">No photos found.</p>';
        return;
    }

    photos.forEach(photo => {
        // Create Item
        const item = document.createElement('div');
        item.className = 'image-item';
        // Add URL data to dataset
        item.dataset.url = photo.url;

        // Base Image
        // Handling paths via Nginx proxy as well
        let imgUrl = photo.url;
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            imgUrl = '/GumaPhoto' + imgUrl;
        }

        // Img tag
        const img = document.createElement('img');
        img.src = imgUrl;
        img.loading = "lazy";

        // Assembly (Pure image without meta tags)
        item.style.position = 'relative';
        item.appendChild(img);

        // Click Event listener logic
        item.addEventListener('click', () => {
            openModal(photo, imgUrl);
        });
        
        grid.appendChild(item);
    });
}


// Upload Logic (Maintained unchanged)
const uploadInput = document.getElementById('upload-input');
const progressContainer = document.getElementById('upload-progress-container');
const progressFill = document.getElementById('progress-bar-fill');
const progressPercent = document.getElementById('progress-percent');
const progressText = document.getElementById('progress-text');

uploadInput.addEventListener('change', async () => {
    const files = uploadInput.files;
    if (files.length === 0) return;

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
});

// ==========================================
// Photo Modal & Feedback Logic
// ==========================================
let currentModalPhoto = null;
const photoModal = document.getElementById('photo-modal');
const modalImage = document.getElementById('modal-image');
const modalClose = document.getElementById('modal-close');
const feedbackBtn = document.getElementById('modal-feedback-btn');
const feedbackContainer = document.getElementById('feedback-container');
const feedbackForm = document.getElementById('feedback-form');
const feedbackInput = document.getElementById('feedback-input');
const feedbackStatus = document.getElementById('feedback-status');
const downloadBtn = document.getElementById('modal-download-btn');
const deleteBtn = document.getElementById('modal-delete-btn');

function openModal(photo, imgUrl) {
    currentModalPhoto = photo;
    modalImage.src = imgUrl;
    photoModal.classList.remove('hidden');
    
    // Reset feedback UI
    feedbackContainer.classList.add('hidden');
    feedbackInput.value = '';
    feedbackInput.disabled = false;
    feedbackStatus.classList.add('hidden');
    
    const submitBtn = document.getElementById('feedback-submit-btn');
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
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

// Feedback 토글 작동
feedbackBtn.addEventListener('click', () => {
    feedbackContainer.classList.toggle('hidden');
    if (!feedbackContainer.classList.contains('hidden')) {
        feedbackInput.focus();
    }
});

// 단일 사진 다운로드 기능
downloadBtn.addEventListener('click', () => {
    if (!currentModalPhoto) return;
    const a = document.createElement('a');
    a.href = modalImage.src;
    a.download = currentModalPhoto.id + '.jpg'; 
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
});

// 삭제 (Hard Delete) 모달 휴지통 버튼 누를 시 발생
deleteBtn.addEventListener('click', async () => {
    if (!currentModalPhoto) return;
    
    if (confirm("Warning: Are you sure you want to permanently delete this photo?\nServer files and AI traces will be completely destroyed.")) {
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
                    filepath: currentModalPhoto.original_path,
                    point_id: currentModalPhoto.id
                })
            });
            
            if (!res.ok) throw new Error("Delete failed");
            
            // DOM에서 방금 지운 사진 타일을 즉시 제거 (새로고침 안 해도 사라지도록)
            const allImages = document.querySelectorAll('.gallery-item img');
            allImages.forEach(img => {
                if(img.src.includes(currentModalPhoto.url)) {
                    img.parentElement.remove();
                }
            });
            
            closeModal();
            alert("Successfully deleted.");
            
        } catch (err) {
            console.error(err);
            alert("Failed to delete. Please contact system administrator.");
        } finally {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
        }
    }
});

feedbackForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = feedbackInput.value.trim();
    if (!text || !currentModalPhoto) return;

    // 현재 사진 경로 (Payload에서 가져온 original_path 우선)
    const photoPath = currentModalPhoto.original_path || currentModalPhoto.url;
    
    // UI 로딩 처리
    feedbackInput.disabled = true;
    const submitBtn = document.getElementById('feedback-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    
    feedbackStatus.classList.remove('hidden');
    feedbackStatus.style.color = 'var(--text-muted)';
    feedbackStatus.innerText = 'AI is analyzing your feedback...';

    try {
        let apiUrl = '/api/feedback';
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            apiUrl = '/GumaPhoto/api/feedback';
        }
        
        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filepath: photoPath,
                point_id: currentModalPhoto.id,
                feedback_text: text
            })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Feedback failed");

        feedbackStatus.style.color = '#10b981'; // Green
        feedbackStatus.innerText = 'Feedback stored in Queue! The global model will learn from this later.';
        
        setTimeout(() => {
            closeModal();
            // 실시간 DB 업데이트를 UI에 반영하기 위해 새로고침하거나 UI 상태를 업데이트 해야 할 수 있지만 일단 모달만 닫음
        }, 2200);

    } catch (err) {
        console.error(err);
        feedbackStatus.style.color = '#ef4444'; // Red
        feedbackStatus.innerText = 'Failed to submit feedback: ' + (err.message || "Try again");
        feedbackInput.disabled = false;
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
    }
});

// ---------------------------------------------------------------------------------
// Live Progress Monitor Logic
// ---------------------------------------------------------------------------------
const progressMonitorBtn = document.getElementById('progress-monitor-btn');
const progressModal = document.getElementById('progress-modal');
const progressModalClose = document.getElementById('progress-modal-close');

let progressPollingInterval = null;

if (progressMonitorBtn) {
    progressMonitorBtn.addEventListener('click', () => {
        progressModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        startProgressPolling();
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
            
            document.getElementById('prog-total').innerText = `${totalPhotos.toLocaleString()} 장`;
            document.getElementById('prog-ai-left').innerText = `${needsDb.toLocaleString()} 장`;
            document.getElementById('prog-db').innerText = `${dbCompleted.toLocaleString()} 장`;
            
            document.getElementById('prog-status').innerHTML = 'Syncing... <i class="fa-solid fa-spinner fa-spin"></i>';
        } else {
            console.error('Failed to load progress data:', res.statusText);
            document.getElementById('prog-status').innerText = 'Waiting (No response data)';
        }
    } catch(err) {
        console.error('Error fetching tracker data:', err);
    }
}

function startProgressPolling() {
    // Immediate fetch
    fetchProgress();
    // Fetch every 2.5 seconds
    progressPollingInterval = setInterval(fetchProgress, 2500);
}
