window.GumaGallery = {};

function renderThemes(themes) {
    const container = document.getElementById('themes-container');
    container.innerHTML = '';

    themes.forEach((theme, idx) => {
        // 프리미엄 레이아웃 믹스: 타일 -> 슬라이딩 -> 슬라이딩 교차 배치
        const isTile = (idx % 3 === 0);

        const section = document.createElement('div');
        section.className = 'theme-section';

        const h3 = document.createElement('h3');
        h3.innerText = theme.title;
        h3.className = 'theme-title';
        section.appendChild(h3);

        const layoutBox = document.createElement('div');
        if (isTile) {
            layoutBox.className = 'theme-tile-box';
            layoutBox.style.display = 'grid';
            layoutBox.style.gridTemplateColumns = 'repeat(3, 1fr)';
            layoutBox.style.gridAutoRows = 'min(30vw, 150px)';
            // 빈 공간을 지능적으로 채우는 매직! (비대칭 레이아웃의 핵심)
            layoutBox.style.gridAutoFlow = 'dense';
            layoutBox.style.gap = '8px';
            layoutBox.style.padding = '0 10px 10px 10px';
        } else {
            layoutBox.className = 'theme-scroll-box';
        }

        const photosToRender = isTile ? theme.photos.slice(0, 8) : theme.photos;

        // 4가지 랜더링 프로파일 (지루하지 않게 순서에 따라 교차 적용)
        let heroIdx = 0, wideIdx = 4;
        const variant = Math.floor(idx / 3) % 4;
        if (variant === 1) { heroIdx = 1; wideIdx = 5; } // 우측 상단 대문
        else if (variant === 2) { heroIdx = 4; wideIdx = 0; } // 우측 하단 대문, 상단 파노라마
        else if (variant === 3) { heroIdx = 3; wideIdx = 7; } // 좌측 중단 대문, 우측 하단 파노라마

        photosToRender.forEach((photo, pIdx) => {
            const imgBtn = document.createElement('div');
            imgBtn.className = 'theme-photo-item';
            imgBtn.dataset.id = photo.id;

            if (isTile) {
                imgBtn.style.borderRadius = '12px';
                imgBtn.style.overflow = 'hidden';
                imgBtn.style.width = '100%';
                imgBtn.style.height = '100%';

                // 크기 변화의 하이라이트 (재미 요소, 다이내믹 퍼즐)
                if (pIdx === heroIdx) {
                    imgBtn.style.gridColumn = 'span 2';
                    imgBtn.style.gridRow = 'span 2';
                } else if (pIdx === wideIdx) {
                    imgBtn.style.gridColumn = 'span 2';
                }
            }

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

            if (isTile) {
                img.style.width = '100%';
                img.style.height = '100%';
                img.style.objectFit = 'cover';
            }

            img.onerror = function () {
                if (this.src !== imgUrl) this.src = imgUrl;
            };
            imgBtn.appendChild(img);

            imgBtn.addEventListener('click', () => {
                openModal(photo, imgUrl);
            });

            layoutBox.appendChild(imgBtn);
        });

        section.appendChild(layoutBox);
        container.appendChild(section);
    });
}

window.GumaGallery.renderThemes = renderThemes;

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

        img.onerror = function () {
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
            let dateVal = (photo.date && photo.date.trim() !== '') ? photo.date : 'Unknown Date';
            if (dateVal.length > 10 && !dateVal.includes('Unknown')) dateVal = dateVal.substring(0, 10);
            badgesHtml += createBadge('fa-regular fa-calendar', dateVal);

            // 2. Location
            let locVal = (photo.location && photo.location.trim() !== '') ? photo.location.replace(/-/g, ' ') : 'Unknown Location';
            if (locVal.includes('위치정보없음') || locVal === 'Unknown') locVal = 'Unknown Location';
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

window.GumaGallery.renderGallery = renderGallery;
