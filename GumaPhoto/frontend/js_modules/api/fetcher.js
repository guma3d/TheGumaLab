/**
 * [API 통신 파트 분리 (Phase 1)]
 * 기존 script_app_v2.js 내부에 혼재되어 있던 모든 fetch 통신을 여기로 분리합니다.
 * UI 조작을 제외하고, 오직 백엔드 서버에서 데이터를 가져오거나 전송하는 역할만 수행합니다.
 */

window.GumaAPI = {};

// 현재 환경 경로 분기 (로컬 개발 시 /api, 실서버 /GumaPhoto/api)
export const getBaseUrl = () => {
    return window.location.pathname.startsWith('/GumaPhoto') ? '/GumaPhoto' : '';
};
window.GumaAPI.getBaseUrl = getBaseUrl;

/**
 * 갤러리 검색/조회 API (메이슨리 이미지 무한 스크롤 용)
 */
export async function apiSearchPhotos(payload, abortSignal = null) {
    const url = `${getBaseUrl()}/api/search`;
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: abortSignal
    });
    
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    return await response.json(); // { results: [], total_hits: 1234, ... }
}
window.GumaAPI.apiSearchPhotos = apiSearchPhotos;

/**
 * 필터 목록(이름, 날짜, 장소) 다운로드
 */
export async function apiGetFilters() {
    const url = `${getBaseUrl()}/api/filters`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('조회 실패');
    return await response.json();
}
window.GumaAPI.apiGetFilters = apiGetFilters;

/**
 * 랜덤 테마 데이터 로드
 */
export async function apiGetThemes(limit = 9) {
    const url = `${getBaseUrl()}/api/themes?limit=${limit}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('테마 로드 실패');
    return await response.json();
}
window.GumaAPI.apiGetThemes = apiGetThemes;

/**
 * 피드백용 후보군 1장 로드 (사람/날짜/장소 모름)
 */
export async function apiGetUnknownPhoto(payload = null) {
    const url = `${getBaseUrl()}/api/feedback_v2/unknown`;
    const options = {
        method: payload ? 'POST' : 'GET',
        headers: { 'Content-Type': 'application/json' }
    };
    if (payload) options.body = JSON.stringify(payload);

    const response = await fetch(url, options);
    if (!response.ok) throw new Error('서버 응답 오류');
    return await response.json();
}
window.GumaAPI.apiGetUnknownPhoto = apiGetUnknownPhoto;

/**
 * 시스템 어드밴스드 통계 다운로드
 */
export async function apiGetAdvancedStats() {
    const url = `${getBaseUrl()}/api/system/advanced`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('통계 로드 실패');
    return await response.json();
}
window.GumaAPI.apiGetAdvancedStats = apiGetAdvancedStats;

