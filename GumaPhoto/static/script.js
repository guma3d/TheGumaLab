let currentQuery = '';
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
    hasMore = true;
    totalHits = 0;
    fetchPhotos(false);
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
        
        if (!res.ok) {
            throw new Error(data.detail || data.error || `HTTP Error ${res.status}`);
        }

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

            if (data.results.length < currentLimit) {
                hasMore = false;
            }
            currentOffset += currentLimit;

            const themesContainer = document.getElementById('themes-container');
            const timelineHeader = document.getElementById('timeline-header');

            if (!currentQuery) {
                // Home Gallery View
                metaContainer.classList.add('hidden');
                if (!isLoadMore && data.themes && data.themes.length > 0) {
                    renderThemes(data.themes);
                    themesContainer.classList.remove('hidden');
                    timelineHeader.classList.remove('hidden');
                } else if (!isLoadMore) {
                    themesContainer.classList.add('hidden');
                    timelineHeader.classList.remove('hidden');
                }
            } else {
                // Search View
                themesContainer.classList.add('hidden');
                timelineHeader.classList.add('hidden');
                
                let fallbackMsg = '';
                if (data.fallback_triggered && !isLoadMore) {
                    fallbackMsg = `<br><span style="color:#ef4444; font-size: 0.9em; margin-top:5px; display:inline-block;">⚠️ '${currentLocation}' 장소에 일치하는 결과가 없어, 유사한 분위기의 사진을 찾았습니다.</span>`;
                }

                metaText.innerHTML = `Found <b style="color:white">${totalHits}</b> photos loaded for: "<i style="color:var(--text-muted)">${currentQuery}</i>" <br> 
                <small style="color:#3b82f6;">(AI parsed: ${currentScene})</small>${fallbackMsg}`;
                metaContainer.classList.remove('hidden');
            }
            
            renderGallery(data.results, isLoadMore);
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

        // Meta tags over image (bottom)
        const infos = document.createElement('div');
        infos.className = 'meta-overlay';
        
        let metaHtml = '';
        
        // 1. 날짜 가공 (YYYY-MM-DD -> YYYY-MM)
        if (photo.date && photo.date.trim() !== '') {
            let shortDate = photo.date;
            if (shortDate.length >= 7) {
                shortDate = shortDate.substring(0, 7); // yyyy-mm
            }
            metaHtml += `<span class="meta-badge"><i class="fa-regular fa-calendar"></i> ${shortDate}</span>`;
        } else {
            metaHtml += `<span class="meta-badge" style="color: #bbb;"><i class="fa-regular fa-calendar"></i> Unknown Date</span>`;
        }
        
        // 2. 시간대 태그 (time_of_day)
        if (photo.time_of_day && photo.time_of_day !== 'Unknown') {
            metaHtml += `<span class="meta-badge"><i class="fa-regular fa-clock"></i> ${photo.time_of_day}</span>`;
        } else {
            metaHtml += `<span class="meta-badge" style="color: #bbb;"><i class="fa-regular fa-clock"></i> Unknown Time</span>`;
        }

        // 3. 계절 태그 (season)
        if (photo.season && photo.season !== 'Unknown') {
            metaHtml += `<span class="meta-badge"><i class="fa-solid fa-leaf"></i> ${photo.season}</span>`;
        } else {
            metaHtml += `<span class="meta-badge" style="color: #bbb;"><i class="fa-solid fa-leaf"></i> Unknown Season</span>`;
        }
        
        // 4. 장소 태그 (Unknown-Location 포함)
        if (photo.location && photo.location.trim() !== '') {
            let prettyLoc = photo.location.replace(/-/g, ' '); // 하이픈을 띄어쓰기로 예쁘게 변환
            metaHtml += `<span class="meta-badge"><i class="fa-solid fa-location-dot"></i> ${prettyLoc}</span>`;
        } else {
            metaHtml += `<span class="meta-badge" style="color: #bbb;"><i class="fa-solid fa-location-dot"></i> Unknown Location</span>`;
        }
        
        // 5. 인물(가족) 태그 - 가장 눈에 띄게 (배경색 강조)
        if (photo.people && photo.people.length > 0) {
            let peopleStr = photo.people.join(', ');
            metaHtml += `<span class="meta-badge" style="background: rgba(59, 130, 246, 0.55); font-weight: 500;"><i class="fa-solid fa-user-tag"></i> ${peopleStr}</span>`;
        } else {
            metaHtml += `<span class="meta-badge" style="background: rgba(75, 85, 99, 0.4); color: #bbb; font-weight: 500;"><i class="fa-solid fa-user-tag"></i> Unknown Person</span>`;
        }

        infos.innerHTML = metaHtml;

        // Score Badge Overlay (Top Left)
        const scoreWrapper = document.createElement('div');
        scoreWrapper.className = 'meta-overlay';
        scoreWrapper.style.top = '0';
        scoreWrapper.style.bottom = 'auto';
        scoreWrapper.style.background = 'linear-gradient(to bottom, rgba(0,0,0,0.6), transparent)';
        // pointer-events: none is already in meta-overlay from CSS
        const scorePercent = (photo.score * 100).toFixed(1);
        scoreWrapper.innerHTML = `<span class="meta-badge" style="background: rgba(16, 185, 129, 0.55); font-weight: 500;"><i class="fa-solid fa-bullseye"></i> 유사율 ${scorePercent}%</span>`;

        // Assembly
        item.style.position = 'relative';
        item.appendChild(img);
        item.appendChild(scoreWrapper);
        if (metaHtml) item.appendChild(infos);

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
    
    if (confirm("🚨 경고: 정말 이 사진을 영구 삭제하시겠습니까?\n서버 원본 파일과 AI DB 흔적까지 모두 파기됩니다.")) {
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
            alert("✅ 완벽하게 삭제(폭파)되었습니다.");
            
        } catch (err) {
            console.error(err);
            alert("❌ 삭제에 실패했습니다. 서버 관리자에게 문의하세요.");
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
            
            // Format numbers with commas (e.g., 14,756)
            const queueCount = Number(data.queue_count || 0).toLocaleString();
            const totalCount = Number(data.total_photos || 0).toLocaleString();
            const dbCount = Number(data.db_completed || 0).toLocaleString();
            
            document.getElementById('prog-queue').innerText = `${queueCount} 장`;
            document.getElementById('prog-total').innerText = `${totalCount} 장`;
            document.getElementById('prog-db').innerText = `${dbCount} 장`;
            
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
