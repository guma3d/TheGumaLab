window.GumaUtils = {};

window.GumaUtils.debounce = (func, delay) => {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => func(...args), delay);
    };
};

window.GumaUtils.isMobileDevice = () => {
    return (window.innerWidth <= 768);
};

window.GumaUtils.extractDateString = (dateStr) => {
    if (!dateStr || dateStr.includes("Unknown")) return 'Unknown Date';
    return dateStr.split(" ")[0];
};

window.GumaUtils.getFilename = (path) => {
    return path ? path.split(/[/\\]/).pop() : 'Unknown';
};

/**
 * 범용 뱃지 생성 유틸 (UI 공통)
 */
window.GumaUtils.createBadge = (icon, text, isHighlight = false) => {
    if (!text || text.includes('Unknown') || text === 'null') return '';
    const highlightClass = isHighlight ? 'highlight-badge' : '';
    return `<span class="meta-badge ${highlightClass}"><i class="${icon}"></i> ${text}</span>`;
};
