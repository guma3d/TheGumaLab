/**
 * [상태 관리 계층 분리 (Phase 2)]
 * 기존 script_app_v2.js 최상단에 선언되었던 전역 변수들을 한곳에 캡슐화.
 */

window.GumaState = {
    currentQuery: '',
    currentGalleryFilter: 'recent',
    currentOffset: 0,
    currentLimit: 20,
    currentPeople: [],
    currentLocation: '',
    currentScene: '',
    isFetching: false,
    hasMore: true,
    totalHits: 0,
    cachedTags: {},
    
    // 피드백/통계 관련 상태
    advancedStatsData: {
        people: [],
        locations: [],
        dates: [],
        scenes: []
    },
    selectedFeedbackTarget: null
};
