window.GumaUpload = {};

// Upload Logic (Maintained unchanged)
const uploadInput = document.getElementById('upload-input');
const progressContainer = document.getElementById('upload-progress-container');
const progressFill = document.getElementById('progress-bar-fill');
const progressPercent = document.getElementById('progress-percent');
const progressText = document.getElementById('progress-text');

async function executeUpload(files) {
    return new Promise((resolve, reject) => {
        if (!files || files.length === 0) return resolve();

        progressContainer.classList.remove('hidden');
        progressFill.style.width = '0%';
        progressPercent.innerText = '0%';
        progressText.innerText = `0 / ${files.length} uploaded`;

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        try {
            let uploadUrl = '/upload/';
            if (window.location.pathname.startsWith('/GumaPhoto')) {
                uploadUrl = '/GumaPhoto/upload/';
            }

            const xhr = new XMLHttpRequest();
            xhr.open('POST', uploadUrl, true);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressFill.style.width = percentComplete + '%';
                    progressPercent.innerText = percentComplete + '%';
                    const filesUploaded = Math.round((files.length * percentComplete) / 100);
                    progressText.innerText = `${filesUploaded} / ${files.length} uploading...`;
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) {
                    progressText.innerText = `${files.length} / ${files.length} successfully uploaded!`;
                    progressFill.style.width = '100%';
                    progressPercent.innerText = '100%';
                    setTimeout(() => { progressContainer.classList.add('hidden'); uploadInput.value = ''; }, 3000);
                    resolve();
                } else {
                    progressText.innerText = 'Upload failed.';
                    progressFill.style.backgroundColor = '#ef4444';
                    reject(new Error("Upload failed"));
                }
            };

            xhr.onerror = () => {
                progressText.innerText = 'Upload error.';
                progressFill.style.backgroundColor = '#ef4444';
                reject(new Error("Network Error"));
            };
            xhr.send(formData);
        } catch (err) {
            console.error(err);
            progressText.innerText = 'Error occurred.';
            reject(err);
        }
    });
}

window.GumaUpload.executeUpload = executeUpload;
window.executeUpload = executeUpload;
