import sys
path = r'd:\TheGumaLab\GumaPhoto\frontend\script_app_v2.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "    const btn = document.getElementById('fb-submit-btn');"
end_marker = "// Kakao Location Autocomplete UI Logic"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Markers not found!")
    sys.exit(1)

new_logic = """    const btn = document.getElementById('fb-submit-btn');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Auto Scanning...';
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

        const data = res.ok ? await res.json() : {results: []};
        
        let targetPoints = [];
        if (data && data.results && data.results.length > 0) {
            targetPoints = data.results.map(item => item.id);
        }

        if (!targetPoints.includes(String(selectedFeedbackTarget.id)) && !targetPoints.includes(Number(selectedFeedbackTarget.id))) {
            targetPoints.push(selectedFeedbackTarget.id);
        }

        console.log("Auto-submitting feedback for targets count:", targetPoints.length);
        await submitSharedFeedback(selectedFeedbackTarget.id, selectedFeedbackTarget.issue, correctValue, targetPoints);

    } catch (err) {
        console.error(err);
        alert("Feedback error: " + err.message);
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
});

// =========================================================================
"""

new_content = content[:start_idx] + new_logic + content[end_idx:]

del_btn_start = "document.getElementById('fb-temptest-send-btn')?.addEventListener('click', async () => {"
del_btn_end = "// 피드백 추가 액션 버튼들"

del_idx_s = new_content.find(del_btn_start)
del_idx_e = new_content.find(del_btn_end)

if del_idx_s != -1 and del_idx_e != -1:
    # also remove the trailing block
    # wait find previous comment to delete completely
    del_header_start = "// =========================================================================\n// 선택된 타겟 대상(체크박스) 피드백 DB 전송 액션"
    del_header_idx = new_content.find(del_header_start)
    if del_header_idx != -1 and del_header_idx < del_idx_s:
        del_idx_s = del_header_idx
        
    new_content = new_content[:del_idx_s] + new_content[del_idx_e:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("UI script updated for auto scan.")
