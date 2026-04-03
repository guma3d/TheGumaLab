import sys
import re

path = r'd:\TheGumaLab\GumaPhoto\frontend\script_app_v2.js'
with open(path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update submitSharedFeedback definition
sig_old = "async function submitSharedFeedback(pointId, issueType, correctValue, targetPointsArray) {"
sig_new = "async function submitSharedFeedback(pointId, issueType, correctValue, targetPointsArray, skipEnrolled = false) {"
js = js.replace(sig_old, sig_new)

payload_old = """            body: JSON.stringify({
                point_id: pointId,
                issue_type: issueType,
                correct_value: correctValue,
                target_points: targetPointsArray
            })"""
payload_new = """            body: JSON.stringify({
                point_id: pointId,
                issue_type: issueType,
                correct_value: correctValue,
                target_points: targetPointsArray,
                skip_enrolled_learning: skipEnrolled
            })"""
js = js.replace(payload_old, payload_new)

# 2. Add visibility toggle for fb-no-learning-btn
toggle_old = """        if (issueType.includes('Person') || issueType.includes('People')) {
            if (personBtns) personBtns.style.display = 'flex';
            if (guideText) guideText.style.display = 'block';
        } else {
            if (personBtns) personBtns.style.display = 'none';
            if (guideText) guideText.style.display = 'none';
        }"""
toggle_new = """        const noLearningBtn = document.getElementById('fb-no-learning-btn');
        if (issueType.includes('Person') || issueType.includes('People')) {
            if (personBtns) personBtns.style.display = 'flex';
            if (guideText) guideText.style.display = 'block';
            if (noLearningBtn) noLearningBtn.style.display = 'block';
        } else {
            if (personBtns) personBtns.style.display = 'none';
            if (guideText) guideText.style.display = 'none';
            if (noLearningBtn) noLearningBtn.style.display = 'none';
        }"""
js = js.replace(toggle_old, toggle_new)

# 3. Add fb-no-learning-btn event listener
listener_code = """
document.getElementById('fb-no-learning-btn')?.addEventListener('click', async () => {
    if (!selectedFeedbackTarget) return;

    const inputVal = document.getElementById('fb-input-val');
    let correctValue = inputVal.value.trim();

    if (!correctValue) {
        alert("Please provide the correct information first!");
        return;
    }

    const btn = document.getElementById('fb-no-learning-btn');
    const ogHtml = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending (No Feedback)...';
    btn.disabled = true;

    try {
        await submitSharedFeedback(selectedFeedbackTarget.id, selectedFeedbackTarget.issue, correctValue, [selectedFeedbackTarget.id], true);
    } catch (err) {
        console.error(err);
        btn.innerHTML = ogHtml;
        btn.disabled = false;
    }
});
"""

# Append listener code at the bottom of the file
js += listener_code

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)
print("JS updated successfully.")
