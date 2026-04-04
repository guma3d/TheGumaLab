window.GumaMonitor = {};

async function updateProgressMonitor() {
    const logBox = document.getElementById('progress-log-content');
    if (!logBox) return;

    let apiUrl = '/api/system/indexer-log';
    if (window.location.pathname.startsWith('/GumaPhoto')) {
        apiUrl = '/GumaPhoto/api/system/indexer-log';
    }

    try {
        const res = await fetch(apiUrl + "?cb=" + new Date().getTime());
        if (res.ok) {
            const data = await res.json();
            logBox.innerHTML = data.log || "No log found or empty.";
            logBox.scrollTop = logBox.scrollHeight; // Auto-scroll to bottom
        } else {
            logBox.innerHTML = "Error fetching log.";
        }
    } catch (e) {
        logBox.innerText = "Network error loading log.";
    }
}

const progressMonitorBtn = document.getElementById('progress-monitor-btn');
if (progressMonitorBtn) {
    progressMonitorBtn.addEventListener('click', () => {
        const modal = document.getElementById('progress-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            updateProgressMonitor(); // Initial fetch
            if (window.progressPollingInterval) clearInterval(window.progressPollingInterval);
            window.progressPollingInterval = setInterval(updateProgressMonitor, 1500); // Poll every 1.5 seconds
        }
    });
}

const progressModalClose = document.getElementById('progress-modal-close');
if (progressModalClose) {
    progressModalClose.addEventListener('click', closeProgressModal);
}

function closeProgressModal() {
    const modal = document.getElementById('progress-modal');
    if (modal) modal.classList.add('hidden');
    document.body.style.overflow = 'auto'; // restore body scroll
    if (window.progressPollingInterval) {
        clearInterval(window.progressPollingInterval);
        window.progressPollingInterval = null;
    }
}

// Close monitor modal when clicking outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('progress-modal');
    if (modal && e.target === modal) {
        closeProgressModal();
    }
});

// Prevent iOS scroll bleed actively on the modal background
const progressModalElement = document.getElementById('progress-modal');
if (progressModalElement) {
    progressModalElement.addEventListener('touchmove', function(e) {
        if (!e.target.closest('#progress-log-content')) {
            e.preventDefault();
        }
    }, { passive: false });
}

window.addEventListener('click', (e) => {
    const statsModal = document.getElementById('stats-modal');
    if (e.target === statsModal) {
        statsModal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
});

GumaState.advancedStatsData = null;

window.fetchAdvancedStats = async function (forceRefresh = false) {
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
            GumaState.advancedStatsData = await res.json();

            const actualLocs = GumaState.advancedStatsData.locations ? GumaState.advancedStatsData.locations.filter(l => !l.name.includes("Unknown") && l.name !== "위치정보없음").length : 0;

            let dateSpanStr = "-";
            if (GumaState.advancedStatsData.min_date && GumaState.advancedStatsData.max_date) {
                const parts1 = GumaState.advancedStatsData.min_date.split("-");
                const parts2 = GumaState.advancedStatsData.max_date.split("-");
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

            document.getElementById('stat-total-photos').innerText = GumaState.advancedStatsData.total_photos.toLocaleString();
            document.getElementById('stat-total-people').innerText = GumaState.advancedStatsData.known_faces_count.toLocaleString();
            document.getElementById('stat-total-locations').innerText = actualLocs.toLocaleString();
            document.getElementById('stat-total-dates').innerText = dateSpanStr;
        }
    } catch (err) {
        console.error('Error fetching advanced stats:', err);
        const refreshIcon = document.getElementById('stats-refresh-icon');
        if (refreshIcon && forceRefresh) refreshIcon.classList.remove('fa-spin');
    }
}

async function fetchAuditLogs() {
    try {
        let apiUrl = '/api/system/audit_logs';
        if (window.location.pathname.startsWith('/GumaPhoto')) apiUrl = '/GumaPhoto' + apiUrl;

        const res = await fetch(apiUrl);
        if (res.ok) {
            const data = await res.json();
            return data;
        }
    } catch (e) {
        console.error('Error fetching audit logs:', e);
    }
    return [];
}

function renderAuditLogs(logs) {
    if (!logs || logs.length === 0) {
        return '<p style="color: #9ca3af; font-size: 0.9rem; text-align: center; padding: 20px 0;">최근 피드백 기록이 없습니다.</p>';
    }

    let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
    logs.forEach(log => {
        const bef = log.before || {};
        const aft = log.after || {};

        const getFilename = window.GumaUtils.getFilename;

        html += `
        <div style="background: rgba(30, 40, 50, 0.4); border-left: 4px solid #8b5cf6; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                <span style="color: white; font-size: 0.9rem; font-family: monospace;">ID: ${log.trace_id.substring(0, 15)}...</span>
                <span style="color: #10b981; font-size: 0.8rem; font-weight: bold;"><i class="fa-solid fa-check"></i> PROCESS DB COMPLETED</span>
            </div>
            
            <div style="display:flex; flex-direction:column; gap:8px; font-size:0.85rem; color:#d1d5db;">
                <div style="display:flex;">
                    <span style="width: 70px; color:#9ca3af;">파일명</span>
                    <span style="flex:1;"><del style="color:#ef4444; margin-right:8px;">${getFilename(bef.filepath)}</del> <i class="fa-solid fa-arrow-right" style="color:#6b7280; font-size:0.7rem; margin-right:8px;"></i> <span style="color:#10b981;">${getFilename(aft.filepath)}</span></span>
                </div>
                <div style="display:flex;">
                    <span style="width: 70px; color:#9ca3af;">날 짜</span>
                    <span style="flex:1;"><del style="color:#ef4444; margin-right:8px;">[${bef.date || 'Unknown'}]</del> <i class="fa-solid fa-arrow-right" style="color:#6b7280; font-size:0.7rem; margin-right:8px;"></i> <span style="color:#10b981;">[${aft.date || 'Unknown'}]</span></span>
                </div>
                <div style="display:flex;">
                    <span style="width: 70px; color:#9ca3af;">장 소</span>
                    <span style="flex:1;"><del style="color:#ef4444; margin-right:8px;">[${bef.location || 'Unknown'}]</del> <i class="fa-solid fa-arrow-right" style="color:#6b7280; font-size:0.7rem; margin-right:8px;"></i> <span style="color:#10b981;">[${aft.location || 'Unknown'}]</span></span>
                </div>
                <div style="display:flex;">
                    <span style="width: 70px; color:#9ca3af;">인 물</span>
                    <span style="flex:1;"><del style="color:#ef4444; margin-right:8px;">${JSON.stringify(bef.people || [])}</del> <i class="fa-solid fa-arrow-right" style="color:#6b7280; font-size:0.7rem; margin-right:8px;"></i> <span style="color:#10b981;">${JSON.stringify(aft.people || [])}</span></span>
                </div>
                
                <div style="margin-top:8px; padding-top:8px; border-top: 1px dashed rgba(255,255,255,0.05); font-size: 0.8rem;">
                    <div style="margin-bottom: 4px;"><span style="color:#f59e0b;">BEFORE EXIF:</span> <span style="color:#9ca3af; font-family:monospace; word-break: break-all;">${bef.exif || 'None'}</span></div>
                    <div><span style="color:#8b5cf6;">AFTER EXIF:</span> <span style="color:#e5e7eb; font-family:monospace; word-break: break-all;">${aft.exif || 'None'}</span></div>
                </div>
            </div>
        </div>
        `;
    });
    html += '</div>';
    return html;
}

window.GumaMonitor.updateProgressMonitor = updateProgressMonitor;
window.updateProgressMonitor = updateProgressMonitor;
window.fetchAuditLogs = fetchAuditLogs;
