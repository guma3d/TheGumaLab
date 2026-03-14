// Search Form Handler
document.getElementById('search-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const query = document.getElementById('search-query').value.trim();
    if (!query) return;

    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const btn = document.getElementById('submit-btn');
    const metaContainer = document.getElementById('search-meta');
    const metaText = document.getElementById('meta-text');
    const grid = document.getElementById('gallery-grid');

    // UI State Start
    btn.disabled = true;
    btnText.style.display = 'none';
    loader.style.display = 'block';
    
    // Clear selection state
    clearSelection();

    try {
        // Build API URL
        let apiUrl = '/api/search';
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            apiUrl = '/GumaPhoto/api/search';
        }

        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        
        const data = await res.json();
        
        if (data.error) {
            metaText.innerHTML = `Error: ${data.error}`;
        } else {
            // Success
            metaText.innerHTML = `Found <b style="color:white">${data.results.length}</b> photos for: "<i style="color:var(--text-muted)">${query}</i>" <br> 
            <small style="color:#3b82f6;">(AI parsed: ${data.enhanced_query})</small>`;
            renderGallery(data.results);
        }
        
        metaContainer.classList.remove('hidden');
        
    } catch (err) {
        console.error(err);
        metaText.innerHTML = 'An expected error occurred while fetching photos.';
        metaContainer.classList.remove('hidden');
    } finally {
        // UI Reset
        btn.disabled = false;
        btnText.style.display = 'block';
        loader.style.display = 'none';
    }
});

let selectedPhotos = new Set();
// Handle Gallery Rendering
function renderGallery(photos) {
    const grid = document.getElementById('gallery-grid');
    grid.innerHTML = ''; // Clear prev

    if (photos.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-muted);">No matching photos found in the multi-modal vector space.</p>';
        return;
    }

    photos.forEach(photo => {
        // Create Item
        const item = document.createElement('div');
        item.className = 'image-item';
        // Add URL data to dataset
        item.dataset.url = photo.url;

        // Base Image
        // Handling paths via Nginx proxy as well
        let imgUrl = photo.url;
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            imgUrl = '/GumaPhoto' + imgUrl;
        }

        // Selection overlay (Checkbox)
        const overlay = document.createElement('div');
        overlay.className = 'selection-overlay';
        overlay.innerHTML = `<div class="custom-checkbox"></div>`;

        // Img tag
        const img = document.createElement('img');
        img.src = imgUrl;
        img.loading = "lazy";

        // Meta tags over image (bottom)
        const infos = document.createElement('div');
        infos.className = 'meta-overlay';
        
        let metaHtml = '';
        if (photo.date) metaHtml += `<span class="meta-badge"><i class="fa-regular fa-calendar"></i> ${photo.date}</span>`;
        if (photo.context) metaHtml += `<span class="meta-badge"><i class="fa-solid fa-folder-open"></i> ${photo.context.split('/').pop()}</span>`;
        if (photo.emotion && photo.emotion !== 'neutral') {
            metaHtml += `<span class="meta-badge"><i class="fa-regular fa-face-smile"></i> ${photo.emotion}</span>`;
        }

        infos.innerHTML = metaHtml;

        // Assembly
        item.appendChild(overlay);
        item.appendChild(img);
        if (metaHtml) item.appendChild(infos);

        // Click Event listener logic
        item.addEventListener('click', () => toggleSelection(item, imgUrl));
        
        grid.appendChild(item);
    });
}

// Selection Logic
function toggleSelection(itemNode, fileUrl) {
    if (selectedPhotos.has(fileUrl)) {
        selectedPhotos.delete(fileUrl);
        itemNode.classList.remove('selected');
    } else {
        selectedPhotos.add(fileUrl);
        itemNode.classList.add('selected');
    }
    updateFAB();
}

function clearSelection() {
    selectedPhotos.clear();
    document.querySelectorAll('.image-item.selected').forEach(el => el.classList.remove('selected'));
    updateFAB();
}

function updateFAB() {
    const fab = document.getElementById('selection-fab');
    const countText = document.getElementById('selection-count');
    
    if (selectedPhotos.size > 0) {
        fab.classList.add('show');
        countText.innerText = `${selectedPhotos.size} Selected`;
    } else {
        fab.classList.remove('show');
    }
}

// Download action (Downloads Array of selected URLs via Backend ZIP route)
document.getElementById('download-btn').addEventListener('click', async () => {
    if (selectedPhotos.size === 0) return;
    
    const countText = document.getElementById('selection-count');
    const btn = document.getElementById('download-btn');
    
    countText.innerText = "Zipping...";
    btn.disabled = true;

    try {
        let apiUrl = '/api/download';
        if (window.location.pathname.startsWith('/GumaPhoto')) {
            apiUrl = '/GumaPhoto/api/download';
        }

        // Extract raw api urls (without GumaPhoto prefix) for backend
        const urlsToDownload = Array.from(selectedPhotos).map(fullUrl => {
            return fullUrl.replace('/GumaPhoto', '');
        });

        const res = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ files: urlsToDownload })
        });

        if (!res.ok) throw new Error("Download Failed");

        // Convert Response to Blob to trigger download
        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = downloadUrl;
        a.download = `GumaPhoto_Selection_${Date.now()}.zip`;
        document.body.appendChild(a);
        a.click();

        window.URL.revokeObjectURL(downloadUrl);
        // Clear UI After successful download
        clearSelection();

    } catch (err) {
        console.error(err);
        alert("Failed to download ZIP.");
    } finally {
        updateFAB();
        btn.disabled = false;
    }
});

document.getElementById('cancel-selection-btn').addEventListener('click', () => {
    clearSelection();
});


// Upload Logic (Maintained unchanged)
const uploadInput = document.getElementById('upload-input');
const progressContainer = document.getElementById('upload-progress-container');
const progressFill = document.getElementById('progress-bar-fill');
const progressPercent = document.getElementById('progress-percent');
const progressText = document.getElementById('progress-text');

uploadInput.addEventListener('change', async () => {
    const files = uploadInput.files;
    if (files.length === 0) return;

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
            } else {
                progressText.innerText = 'Upload failed.';
                progressFill.style.backgroundColor = '#ef4444';
            }
        };

        xhr.onerror = () => { progressText.innerText = 'Upload error.'; progressFill.style.backgroundColor = '#ef4444'; };
        xhr.send(formData);
    } catch (err) {
        console.error(err);
        progressText.innerText = 'Error occurred.';
    }
});
