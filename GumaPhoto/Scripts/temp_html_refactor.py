import os

file_path = r"d:\TheGumaLab\GumaPhoto\templates\index.html"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# Wrap main gallery elements in #home and inject #feedback, #upload, #system into <main>
main_start = html.find('<!-- Gallery Slider Content (Now directly under header) -->')
main_end = html.find('</main>', main_start)

if main_start != -1 and main_end != -1:
    extracted_main = html[main_start:main_end]
    
    new_main_content = f"""<!-- Home Tab -->
            <div id="home">
                {extracted_main}
            </div>

            <!-- Feedback Tab -->
            <div id="feedback" class="hidden" style="max-width: 500px; margin: 0 auto; padding-top: 2rem;">
                <h2 style="font-size: 1.5rem; margin-bottom: 1rem; color: #10b981; font-weight: 800;"><i class="fa-solid fa-graduation-cap"></i> 자율 진화 학습 (1장 교정)</h2>
                <p style="color: var(--text-muted); margin-bottom: 1.5rem; font-size: 0.9rem; line-height: 1.4;">정보가 누락된 단 1장의 사진입니다. 정답을 적어주시면 AI가 주변 상황을 파악해 나머지 사진들까지 스스로 고칩니다!</p>

                <div id="fb-unknown-photo-container" style="display: flex; flex-direction: column; align-items: center; gap: 15px; width: 100%;">
                    <!-- 1 Photo Showcase -->
                    <div style="width: 100%; border-radius: 12px; overflow: hidden; background: rgba(0,0,0,0.5); border: 1px solid var(--glass-border); display: flex; justify-content: center; align-items: center; min-height: 250px;">
                        <img id="fb-target-img" src="" alt="Unknown Photo" style="max-width: 100%; max-height: 350px; object-fit: contain; display: none;">
                        <span id="fb-loading-spinner" style="font-size: 2.5rem; color: #10b981;"><i class="fa-solid fa-spinner fa-spin"></i></span>
                    </div>
                    <!-- Issue Type Tag -->
                    <div id="fb-target-issue" style="background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.5); color: #fca5a5; padding: 6px 12px; border-radius: 999px; font-weight: bold; font-size: 0.9rem; display: none;">
                        <i class="fa-solid fa-circle-exclamation"></i> 장소 정보 누락
                    </div>
                    <!-- Input area -->
                    <div id="fb-single-input-area" style="width: 100%; display: flex; flex-direction: column; gap: 10px; margin-top: 5px;">
                        <input type="text" id="fb-input-val" placeholder="정답을 입력하세요 (예: 성욱, 미국-하와이)" style="padding: 14px; border-radius: 8px; border: 1px solid var(--glass-border); background: var(--surface-dark); color: white; font-size: 1rem;" autocomplete="off">
                        <input type="month" id="fb-input-date" style="padding: 14px; border-radius: 8px; border: 1px solid var(--glass-border); background: var(--surface-dark); color: white; font-size: 1rem; display: none;">
                        <button id="fb-submit-btn" class="primary-btn" style="padding: 12px; font-weight: 800; background: #10b981; border: none; font-size: 1.1rem; border-radius: 8px; color: #000; margin-top: 5px;"><i class="fa-solid fa-check"></i> 자율 전파(Propagation) 승인</button>
                        <button id="fb-skip-btn" class="secondary-btn" style="padding: 10px; font-size: 0.95rem; color: var(--text-muted); background: transparent; border: 1px solid var(--glass-border); border-radius: 8px;">모르겠어요 (다음 사진)</button>
                    </div>
                </div>
            </div>

            <!-- Upload Tab -->
            <div id="upload" class="hidden" style="display:flex; flex-direction:column; align-items:center; padding-top: 10vh; gap: 20px;">
                <i class="fa-solid fa-cloud-arrow-up" style="font-size: 4rem; color: #3b82f6;"></i>
                <h2 style="color: white; font-size: 1.5rem; margin: 0;">사진 데스크 업로드</h2>
                <p style="color: var(--text-muted); text-align: center;">휴대폰에 저장된 새로운 사진들을 GumaPhoto로 전송합니다.</p>
                <div id="local-upload-preview" style="display:flex; flex-wrap:wrap; gap:10px; justify-content:center; max-width: 600px; max-height: 40vh; overflow-y: auto;">
                    <!-- JS renders selected local photos here -->
                </div>
                <button class="primary-btn" onclick="document.getElementById('upload-input').click()" style="padding: 14px 24px; font-size: 1.1rem; border-radius: 999px; margin-top: 20px; font-weight: 800;">
                    <i class="fa-solid fa-folder-open"></i> 스마트폰 갤러리 열기
                </button>
            </div>

            <!-- System Tab -->
            <div id="system" class="hidden" style="max-width: 400px; margin: 0 auto; box-sizing: border-box; padding: 2rem 0; text-align: center;">
                <h2 style="font-size: 1.8rem; color: white; display:flex; justify-content:center; align-items:center; gap: 8px; margin-bottom: 1.8rem; font-weight: 800;">
                    <i class="fa-solid fa-server"></i> DB Status
                </h2>
                <div style="display:flex; flex-direction: column; gap: 12px; text-align: center;">
                    <div style="background: var(--surface-light); padding: 16px; border-radius: 8px;">
                        <h3 style="color:var(--text-muted); font-size: 1.2rem; margin-bottom: 6px;">Total Server Photos</h3>
                        <p id="prog-total" style="color:#3b82f6; font-size: 1.5rem; font-weight:bold;">Loading...</p>
                        <small style="font-size: 0.9rem; color: #aaa;">Total pure image files stored in server</small>
                    </div>
                    <div style="background: var(--surface-light); padding: 16px; border-radius: 8px;">
                        <h3 style="color:var(--text-muted); font-size: 1.2rem; margin-bottom: 6px;">Pending DB Generation</h3>
                        <p id="prog-ai-left" style="color:#ef4444; font-size: 1.5rem; font-weight:bold;">Loading...</p>
                        <small style="font-size: 0.9rem; color: #aaa;">Images waiting for AI vector indexing</small>
                    </div>
                    <div style="background: var(--surface-light); padding: 16px; border-radius: 8px;">
                        <h3 style="color:var(--text-muted); font-size: 1.2rem; margin-bottom: 6px;">Completed Photos</h3>
                        <p id="prog-db" style="color:#10b981; font-size: 1.5rem; font-weight:bold;">Loading...</p>
                        <small style="font-size: 0.9rem; color: #aaa;">Photos fully analyzed and searchable</small>
                    </div>
                    <p id="prog-status" style="font-size: 0.85rem; color: var(--text-muted); text-align:center; margin-top: 10px;">
                        Syncing...
                    </p>
                </div>
            </div>
        """
    
    html = html[:main_start] + new_main_content + html[main_end:]

# Now surgically remove the old #progress-modal and #feedback-hub-modal DOM elements!
import re
html = re.sub(r'<!-- Live Progress Monitor Modal -->\s*<div id="progress-modal".*?</div>\s*</div>\s*(?=<!-- Self-Healing Feedback Modal v2 -->)', '', html, flags=re.DOTALL)
html = re.sub(r'<!-- Self-Healing Feedback Modal v2 -->\s*<div id="feedback-hub-modal".*?</div>\s*</div>\s*(?=<!-- Custom Delete Confirmation Modal -->)', '', html, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
