import os
import re

file_path = r"d:\TheGumaLab\GumaPhoto\static\script.js"
with open(file_path, "r", encoding="utf-8") as f:
    js = f.read()

# Add switchView function
switch_view_code = """
// =========================================================================
// 📱 Mobile Bottom Navigation Bar & View Router Logic
// =========================================================================
const views = ['home', 'feedback', 'upload', 'system'];

function switchView(target) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    views.forEach(v => {
        const el = document.getElementById(v);
        if (el) {
            if (v === target) {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        }
    });

    document.querySelectorAll('.bottom-nav .nav-item').forEach(item => {
        if (item.id === `nav-${target}-btn`) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}
"""

# Replace the Mobile Bottom Nav logic at the EOF with our new logic
js = re.sub(r'// =========================================================================\s+// 📱 Mobile Bottom Navigation Bar Logic\s+// =========================================================================.*', switch_view_code, js, flags=re.DOTALL)

# Add scroll listener back
scroll_logic = """
const bottomNav = document.getElementById('bottom-nav');
let lastScrollY = window.scrollY;

if (bottomNav) {
    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        // 아이폰 바운스 스크롤 효과 방어용
        if (currentScrollY <= 0) {
            bottomNav.classList.remove('nav-hidden');
        } else if (currentScrollY > lastScrollY && currentScrollY > 25) {
            bottomNav.classList.add('nav-hidden');
        } else if (currentScrollY < lastScrollY) {
            bottomNav.classList.remove('nav-hidden');
        }
        
        lastScrollY = currentScrollY;
    }, { passive: true });
    
    document.getElementById('nav-home-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('home');
    });
    
    document.getElementById('nav-feedback-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('feedback');
        loadFeedbackTarget();
    });
    
    document.getElementById('nav-upload-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('upload');
    });
    
    document.getElementById('nav-system-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchView('system');
        updateProgressMonitor(); // fetch system status when tab is opened
    });
}
"""
js += scroll_logic

# Update header buttons to use switchView instead of opening modals
js = js.replace("document.getElementById('feedback-hub-modal').classList.remove('hidden');", "switchView('feedback');")
js = js.replace("document.getElementById('progress-modal').classList.remove('hidden');", "switchView('system');")

# Remove old modal close event listeners for system and feedback since they are no longer modals
js = re.sub(r"document\.getElementById\('feedback-hub-close'\)\?\.addEventListener[^}]+}\);", "", js)
js = re.sub(r"document\.getElementById\('progress-modal-close'\)\?\.addEventListener[^}]+}\);", "", js)

# Local photo preview generation logic for Upload View
local_upload_js = """
// =========================================================================
// Upload View Local Preview
// =========================================================================
document.getElementById('upload-input')?.addEventListener('change', function(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    const previewContainer = document.getElementById('local-upload-preview');
    if (previewContainer) {
        previewContainer.innerHTML = '';
        const limit = Math.min(files.length, 12); // limit preview to 12
        for (let i = 0; i < limit; i++) {
            const file = files[i];
            const imgUrl = URL.createObjectURL(file);
            const imgElement = document.createElement('img');
            imgElement.src = imgUrl;
            imgElement.style.width = '100px';
            imgElement.style.height = '100px';
            imgElement.style.objectFit = 'cover';
            imgElement.style.borderRadius = '8px';
            previewContainer.appendChild(imgElement);
        }
        if (files.length > limit) {
            const moreIndicator = document.createElement('div');
            moreIndicator.style.width = '100px';
            moreIndicator.style.height = '100px';
            moreIndicator.style.borderRadius = '8px';
            moreIndicator.style.background = 'rgba(255,255,255,0.1)';
            moreIndicator.style.display = 'flex';
            moreIndicator.style.alignItems = 'center';
            moreIndicator.style.justifyContent = 'center';
            moreIndicator.style.color = '#fff';
            moreIndicator.style.fontWeight = 'bold';
            moreIndicator.innerHTML = `+${files.length - limit} 장`;
            previewContainer.appendChild(moreIndicator);
        }
        
        // Append Upload action to start uploading directly from preview
        const actionArea = document.createElement('div');
        actionArea.style.width = '100%';
        actionArea.style.textAlign = 'center';
        actionArea.style.marginTop = '15px';
        const startBtn = document.createElement('button');
        startBtn.className = 'primary-btn';
        startBtn.style.padding = '12px 24px';
        startBtn.style.background = '#10b981';
        startBtn.style.borderRadius = '999px';
        startBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> 선택 항목 업로드 (' + files.length + '장)';
        startBtn.onclick = async () => {
            // We reuse the existing upload execution logic
            // Since upload-input changed, it might have already started uploading if we didn't decouple it!
            // Wait, existing upload logic in script.js listens to upload-input 'change' too!
        };
        // wait, we need to handle existing upload handler...
    }
});
"""

# Actually, the existing script.js has an event listener for 'upload-input' 'change' that starts uploading automatically.
# I need to decouple it, so 'upload-input' ONLY previews, and then we add a custom upload action.
# Let's find existing upload logic.
old_upload = "document.getElementById('upload-input').addEventListener('change', async function(e) {"
new_upload = "async function executeUpload(files) {"
js = js.replace(old_upload, new_upload)

# We need to wire UI to fire executeUpload
local_upload_js = """
// =========================================================================
// Upload View Local Preview & Execution
// =========================================================================
document.getElementById('upload-input')?.addEventListener('change', function(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    // Check if we are in upload view. If we triggered from top header, maybe just upload directly?
    // Let's always route to upload view nicely.
    switchView('upload');
    
    const previewContainer = document.getElementById('local-upload-preview');
    if (previewContainer) {
        previewContainer.innerHTML = '';
        const limit = Math.min(files.length, 12);
        for (let i = 0; i < limit; i++) {
            const file = files[i];
            const imgUrl = URL.createObjectURL(file);
            const imgElement = document.createElement('img');
            imgElement.src = imgUrl;
            imgElement.style.width = '100px';
            imgElement.style.height = '100px';
            imgElement.style.objectFit = 'cover';
            imgElement.style.borderRadius = '8px';
            imgElement.style.border = '1px solid rgba(255,255,255,0.1)';
            previewContainer.appendChild(imgElement);
        }
        if (files.length > limit) {
            const moreIndicator = document.createElement('div');
            moreIndicator.style.width = '100px';
            moreIndicator.style.height = '100px';
            moreIndicator.style.borderRadius = '8px';
            moreIndicator.style.background = 'rgba(255,255,255,0.1)';
            moreIndicator.style.display = 'flex';
            moreIndicator.style.alignItems = 'center';
            moreIndicator.style.justifyContent = 'center';
            moreIndicator.style.color = '#fff';
            moreIndicator.style.fontWeight = 'bold';
            moreIndicator.innerHTML = `+${files.length - limit}`;
            previewContainer.appendChild(moreIndicator);
        }
        
        let existingBtn = document.getElementById('execute-upload-btn');
        if (existingBtn) existingBtn.remove();
        
        const startBtn = document.createElement('button');
        startBtn.id = 'execute-upload-btn';
        startBtn.className = 'primary-btn';
        startBtn.style.padding = '12px 24px';
        startBtn.style.background = '#10b981';
        startBtn.style.borderRadius = '999px';
        startBtn.style.border = 'none';
        startBtn.style.marginTop = '20px';
        startBtn.style.fontSize = '1.1rem';
        startBtn.style.fontWeight = 'bold';
        startBtn.style.cursor = 'pointer';
        startBtn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> 서버로 전송 (' + files.length + '장)';
        // Append underneath the preview
        previewContainer.parentElement.appendChild(startBtn);
        
        startBtn.onclick = async () => {
             startBtn.disabled = true;
             startBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 업로드 진행 중...';
             await executeUpload(files); // Run the existing massive upload chunk properly!
             startBtn.innerHTML = '<i class="fa-solid fa-check"></i> 전송 완료';
             setTimeout(() => switchView('home'), 1500);
        };
    }
});
"""

js += local_upload_js

with open(file_path, "w", encoding="utf-8") as f:
    f.write(js)
