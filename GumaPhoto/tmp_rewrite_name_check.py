import sys

path = r'd:\TheGumaLab\GumaPhoto\frontend\script_app_v2.js'
with open(path, 'r', encoding='utf-8') as f:
    js = f.read()

target = """    if (!correctValue) {
        alert("Please provide the correct information first!");
        return;
    }"""

# New logic for confirming unknown person names
replacement = """    if (!correctValue) {
        alert("Please provide the correct information first!");
        return;
    }

    // Check for unregistered names
    if (selectedFeedbackTarget && (selectedFeedbackTarget.issue.includes('Person') || selectedFeedbackTarget.issue.includes('People'))) {
        let isKnown = false;
        if (typeof advancedStatsData !== 'undefined' && advancedStatsData.people) {
            isKnown = advancedStatsData.people.some(p => p.name === correctValue);
        }
        if (!isKnown) {
            const confirmed = confirm(`'${correctValue}'님은 기존에 등록된 이름이 아닙니다.\\n오타가 아니라면 새로 추가하시겠습니까?`);
            if (!confirmed) return;
        }
    }"""

js = js.replace(target, replacement) # Replaces it for BOTH fb-submit-btn and fb-no-learning-btn because the target string appears twice or if it appears twice, it'll replace all.

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Injected name verification logic.")
