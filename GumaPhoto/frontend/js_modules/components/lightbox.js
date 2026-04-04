// ==========================================
// Photo Modal & Feedback Variables Definitions
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
if (modalImage) {
    modalImage.addEventListener('click', () => {
        if (modalInfoBadges) modalInfoBadges.classList.toggle('hidden');
        if (modalActionsCenter) modalActionsCenter.classList.toggle('hidden');
    });
}

window.GumaLightbox = {};
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
        alert("성공적으로 삭제되었습니다.");

    } catch (err) {
        console.error(err);
        alert(`삭제 실패: ${err.message || '알 수 없는 오류가 발생했습니다.'}`);
    } finally {
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
    }
});

// ---------------------------------------------------------------------------------

window.GumaLightbox.openModal = openModal;
window.openModal = openModal;
window.closeModal = closeModal;
