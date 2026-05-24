document.addEventListener("DOMContentLoaded", () => {
    const BASE_URL = window.location.pathname.endsWith("/") ? window.location.pathname : window.location.pathname + "/";

    const form = document.getElementById("topic-form");
    const topicInput = document.getElementById("topic-input");
    const gradeSelect = document.getElementById("grade-select");
    const quizCountSelect = document.getElementById("quiz-count-select");
    const submitBtn = document.getElementById("submit-btn");
    const btnText = submitBtn.querySelector(".btn-text");
    const loader = submitBtn.querySelector(".loader");

    const statusPanel = document.getElementById("status-panel");
    const statusText = document.getElementById("status-text");
    const progressFill = document.getElementById("progress-fill");
    const progressPercent = document.getElementById("progress-percent");
    const resultContainer = document.getElementById("result-container");
    const resultActions = document.getElementById("result-actions");

    const activeSection = document.getElementById("active-section");
    const activeList = document.getElementById("active-list");
    const tasksList = document.getElementById("tasks-list");

    const searchModal = document.getElementById("search-modal");
    const openSearchModalBtn = document.getElementById("open-search-modal-btn");
    const closeSearchModalBtn = document.getElementById("close-search-modal-btn");
    const searchInput = document.getElementById("search-input");
    const documentSearchBtn = document.getElementById("document-search-btn");

    let pollingTimer = null;
    let searchQuery = "";

    loadTasks();
    setInterval(loadTasks, 3000);

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const topic = topicInput.value.trim();
        if (!topic) return;

        setBusy(true);
        resultContainer.classList.add("hidden");
        statusPanel.classList.remove("hidden");
        updateProgress(5, "Requesting document generation...");

        try {
            const response = await fetch(BASE_URL + "process", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-Source": "web" },
                body: JSON.stringify({
                    topic,
                    grade: gradeSelect.value,
                    quiz_count: Number(quizCountSelect.value),
                }),
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || "Failed to process request.");
            }
            updateProgress(10, "Request received! Task queued.");
            startPolling(data.task_id);
            loadTasks();
        } catch (error) {
            handleError(error.message);
        }
    });

    if (openSearchModalBtn && searchModal) {
        openSearchModalBtn.addEventListener("click", () => {
            searchModal.classList.add("open");
            searchInput.value = searchQuery;
            searchInput.focus();
        });
    }

    if (closeSearchModalBtn && searchModal) {
        closeSearchModalBtn.addEventListener("click", () => {
            searchModal.classList.remove("open");
        });
    }

    if (searchModal) {
        searchModal.addEventListener("click", (event) => {
            if (event.target === searchModal) {
                searchModal.classList.remove("open");
            }
        });
    }

    if (documentSearchBtn && searchInput) {
        documentSearchBtn.addEventListener("click", applySearch);
        searchInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") applySearch();
        });
    }

    function applySearch() {
        searchQuery = searchInput.value.trim().toLowerCase();
        searchModal.classList.remove("open");
        loadTasks();
    }

    function setBusy(isBusy) {
        topicInput.disabled = isBusy;
        gradeSelect.disabled = isBusy;
        quizCountSelect.disabled = isBusy;
        submitBtn.disabled = isBusy;
        btnText.style.display = isBusy ? "none" : "block";
        loader.style.display = isBusy ? "block" : "none";
    }

    function updateProgress(percent, text) {
        const safePercent = Math.max(0, Math.min(Number(percent) || 0, 100));
        progressFill.style.width = `${safePercent}%`;
        progressPercent.textContent = `${Math.round(safePercent)}%`;
        statusText.textContent = text;
        statusText.style.color = "";
        progressFill.style.backgroundColor = "";
    }

    function handleError(message) {
        statusPanel.classList.remove("hidden");
        statusText.textContent = `Error: ${message}`;
        statusText.style.color = "var(--danger)";
        progressFill.style.backgroundColor = "var(--danger)";
        progressPercent.textContent = "Failed";
        setBusy(false);
    }

    function showResult(taskId) {
        statusPanel.classList.add("hidden");
        resultActions.innerHTML = `
            <button type="button" onclick="window.open('${BASE_URL}view/${taskId}', '_blank')">
                <i class="fa-solid fa-up-right-from-square"></i> View
            </button>
            <button type="button" onclick="window.location.href='${BASE_URL}download/${taskId}'">
                <i class="fa-solid fa-download"></i> Download
            </button>
        `;
        resultContainer.classList.remove("hidden");
        setBusy(false);
        topicInput.value = "";
    }

    function startPolling(taskId) {
        if (pollingTimer) clearInterval(pollingTimer);

        pollingTimer = setInterval(async () => {
            try {
                const response = await fetch(`${BASE_URL}task/${taskId}`);
                const task = await response.json();
                if (task.error && !task.status) throw new Error(task.error);

                const percent = Number(task.percent || 0);
                updateProgress(percent, task.progress || task.status || "Processing...");

                if (task.status === "completed") {
                    clearInterval(pollingTimer);
                    pollingTimer = null;
                    updateProgress(100, "Document generation complete!");
                    setTimeout(() => showResult(taskId), 600);
                    loadTasks();
                } else if (task.status === "failed") {
                    clearInterval(pollingTimer);
                    pollingTimer = null;
                    handleError(task.error || "Processing failed.");
                    loadTasks();
                }
            } catch (error) {
                clearInterval(pollingTimer);
                pollingTimer = null;
                handleError(error.message);
            }
        }, 1200);
    }

    async function loadTasks() {
        try {
            const response = await fetch(BASE_URL + "tasks");
            const data = await response.json();
            const tasks = Array.isArray(data.tasks) ? data.tasks : [];
            const active = tasks.filter((task) => ["queued", "processing"].includes(task.status));
            let completed = tasks.filter((task) => task.status === "completed");

            if (searchQuery) {
                completed = completed.filter((task) => {
                    const text = `${task.topic || ""} ${task.grade || ""} ${task.result?.title || ""}`.toLowerCase();
                    return text.includes(searchQuery);
                });
            }

            renderActive(active);
            renderHistory(completed);
        } catch (error) {
            tasksList.innerHTML = `<p class="empty">Failed to load documents. ${escapeHtml(error.message)}</p>`;
        }
    }

    function renderActive(tasks) {
        activeSection.classList.toggle("hidden", tasks.length === 0);
        activeList.innerHTML = tasks.map(createActiveTaskCard).join("");
    }

    function renderHistory(tasks) {
        if (!tasks.length) {
            tasksList.innerHTML = `<p class="empty">No documents found.</p>`;
            return;
        }
        tasksList.innerHTML = tasks.map(createTaskCard).join("");
    }

    function createActiveTaskCard(task) {
        const title = task.result?.title || task.topic || "Untitled Topic";
        const isProcessing = task.status === "processing";
        const statusClass = isProcessing ? "processing" : "";
        const statusLabel = isProcessing ? "Processing" : "Queued";
        const progressLog = task.progress || "Waiting...";

        return `
            <div class="active-task-item ${statusClass}">
                <div class="active-thumb"><i class="fa-solid fa-book-open"></i></div>
                <div class="active-info">
                    <div class="active-title">${escapeHtml(title)}</div>
                    <div class="active-log">
                        <i class="fa-solid ${isProcessing ? "fa-circle-notch fa-spin" : "fa-hourglass-half"}"></i>
                        ${escapeHtml(progressLog)}
                    </div>
                </div>
                <div class="active-status">${statusLabel}</div>
            </div>
        `;
    }

    function createTaskCard(task) {
        const title = task.result?.title || task.topic || "Untitled Topic";
        const createdAt = formatDate(task.created_at);
        const meta = [task.grade, createdAt].filter(Boolean).join(" · ");
        const thumbnailUrl = task.result?.thumbnail_url || "";
        const thumbnailHtml = thumbnailUrl
            ? `<img src="${escapeAttribute(thumbnailUrl)}" alt="${escapeAttribute(title)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentElement.innerHTML='<i class=&quot;fa-solid fa-file-lines&quot;></i>';">`
            : `<i class="fa-solid fa-file-lines"></i>`;

        return `
            <article class="grid-card">
                <a href="${BASE_URL}view/${task.task_id}" target="_blank" class="card-main">
                    <div class="card-thumb">${thumbnailHtml}</div>
                    <div class="card-content">
                        <div class="card-title">${escapeHtml(title)}</div>
                        <div class="card-meta">${escapeHtml(meta)}</div>
                    </div>
                </a>
                <div class="task-actions">
                    <button type="button" onclick="window.open('${BASE_URL}view/${task.task_id}', '_blank')">
                        <i class="fa-solid fa-up-right-from-square"></i>
                    </button>
                    <button type="button" onclick="window.location.href='${BASE_URL}download/${task.task_id}'">
                        <i class="fa-solid fa-download"></i>
                    </button>
                    <button type="button" class="danger" onclick="deleteTask('${task.task_id}')">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </article>
        `;
    }

    function formatDate(value) {
        if (!value) return "";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString("ko-KR", {
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function escapeHtml(value) {
        return String(value || "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function escapeAttribute(value) {
        return escapeHtml(value).replaceAll("`", "&#096;");
    }

    window.deleteTask = async (taskId) => {
        if (!confirm("저장된 HTML과 기록을 삭제할까요?")) return;
        const response = await fetch(`${BASE_URL}delete/${taskId}`, { method: "POST" });
        const data = await response.json();
        if (!data.success) alert(data.error || "삭제에 실패했습니다.");
        loadTasks();
    };
});
