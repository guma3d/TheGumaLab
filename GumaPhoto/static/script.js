document.getElementById('search-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const query = document.getElementById('search-query').value.trim();
    if (!query) return;

    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const btn = document.getElementById('submit-btn');
    const resultContainer = document.getElementById('result-container');

    // Simulate search loading state
    btn.disabled = true;
    btnText.style.display = 'none';
    loader.style.display = 'block';
    
    setTimeout(() => {
        // Reset button
        btn.disabled = false;
        btnText.style.display = 'block';
        loader.style.display = 'none';
        
        // Show simulated result
        resultContainer.classList.remove('hidden');
        document.querySelector('.result-msg').innerHTML = `Search simulated for: "<b>${query}</b>"<br>Images will be displayed here eventually!`;
    }, 1500);
});

// 업로드 로직
const uploadBtn = document.getElementById('upload-btn');
const uploadInput = document.getElementById('upload-input');
const progressContainer = document.getElementById('upload-progress-container');
const progressFill = document.getElementById('progress-bar-fill');
const progressPercent = document.getElementById('progress-percent');
const progressText = document.getElementById('progress-text');

uploadBtn.addEventListener('click', () => {
    uploadInput.click();
});

uploadInput.addEventListener('change', async () => {
    const files = uploadInput.files;
    if (files.length === 0) return;

    // UI 초기화
    progressContainer.classList.remove('hidden');
    progressFill.style.width = '0%';
    progressPercent.innerText = '0%';
    progressText.innerText = `0 / ${files.length} uploaded`;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        // XMLHttpRequest를 사용해 실제 진행률 트래킹
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload/', true);

        // 진행률 업데이트 이벤트
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressFill.style.width = percentComplete + '%';
                progressPercent.innerText = percentComplete + '%';
                // 좀 더 자연스러운 텍스트를 위해 퍼센트로 파일 수 근사치 표시
                const filesUploaded = Math.round((files.length * percentComplete) / 100);
                progressText.innerText = `${filesUploaded} / ${files.length} uploading...`;
            }
        };

        xhr.onload = () => {
            if (xhr.status === 200) {
                progressText.innerText = `${files.length} / ${files.length} successfully uploaded!`;
                progressFill.style.width = '100%';
                progressPercent.innerText = '100%';
                
                // 3초 후 UI 닫기
                setTimeout(() => {
                    progressContainer.classList.add('hidden');
                    uploadInput.value = ''; // 초기화
                }, 3000);
            } else {
                progressText.innerText = 'Upload failed.';
                progressFill.style.backgroundColor = '#ef4444'; // 에러 레드
            }
        };

        xhr.onerror = () => {
            progressText.innerText = 'Upload error.';
            progressFill.style.backgroundColor = '#ef4444';
        };

        xhr.send(formData);

    } catch (err) {
        console.error(err);
        progressText.innerText = 'Error occurred.';
    }
});
