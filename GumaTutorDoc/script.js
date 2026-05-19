document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("topic-form");
  const topicInput = document.getElementById("topic-input");
  const gradeSelect = document.getElementById("grade-select");
  const quizCountSelect = document.getElementById("quiz-count-select");
  const submitBtn = document.getElementById("submit-btn");

  const statusPanel = document.getElementById("status-panel");
  const statusTopic = document.getElementById("status-topic");
  const statusText = document.getElementById("status-text");
  const progressFill = document.getElementById("progress-fill");
  const progressPercent = document.getElementById("progress-percent");
  const resultActions = document.getElementById("result-actions");

  const activeSection = document.getElementById("active-section");
  const activeList = document.getElementById("active-list");
  const tasksList = document.getElementById("tasks-list");
  const searchInput = document.getElementById("search-input");

  let pollingTimer = null;
  let searchQuery = "";

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const topic = topicInput.value.trim();
    if (!topic) return;

    setBusy(true);
    showStatus(topic, 5, "요청을 보내는 중...");

    try {
      const response = await fetch("process", {
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
        throw new Error(data.error || "생성 요청에 실패했습니다.");
      }
      startPolling(data.task_id);
      loadTasks();
    } catch (error) {
      showStatus(topic, 100, `오류: ${error.message}`);
      setBusy(false);
    }
  });

  searchInput.addEventListener("input", () => {
    searchQuery = searchInput.value.trim().toLowerCase();
    loadTasks();
  });

  function setBusy(isBusy) {
    topicInput.disabled = isBusy;
    gradeSelect.disabled = isBusy;
    quizCountSelect.disabled = isBusy;
    submitBtn.disabled = isBusy;
  }

  function showStatus(topic, percent, text) {
    statusPanel.classList.remove("hidden");
    statusTopic.textContent = topic;
    progressFill.style.width = `${Math.max(0, Math.min(percent, 100))}%`;
    progressPercent.textContent = `${Math.round(percent)}%`;
    statusText.textContent = text;
    resultActions.classList.add("hidden");
    resultActions.innerHTML = "";
  }

  function showResult(taskId) {
    resultActions.innerHTML = `
      <button type="button" class="secondary-btn" onclick="window.open('view/${taskId}', '_blank')">
        <span class="btn-icon" aria-hidden="true">↗</span>
        열기
      </button>
      <button type="button" class="secondary-btn" onclick="window.location.href='download/${taskId}'">
        <span class="btn-icon" aria-hidden="true">↓</span>
        다운로드
      </button>
    `;
    resultActions.classList.remove("hidden");
  }

  function startPolling(taskId) {
    if (pollingTimer) clearInterval(pollingTimer);
    pollingTimer = setInterval(async () => {
      try {
        const response = await fetch(`task/${taskId}`);
        const task = await response.json();
        if (task.error && !task.status) throw new Error(task.error);

        const percent = Number(task.percent || 0);
        showStatus(task.topic || "처리 중", percent, task.progress || task.status || "처리 중...");

        if (task.status === "completed") {
          clearInterval(pollingTimer);
          pollingTimer = null;
          showStatus(task.topic, 100, "HTML 저장 완료");
          showResult(taskId);
          setBusy(false);
          topicInput.value = "";
          loadTasks();
        } else if (task.status === "failed") {
          clearInterval(pollingTimer);
          pollingTimer = null;
          showStatus(task.topic, 100, task.error || "생성에 실패했습니다.");
          setBusy(false);
          loadTasks();
        }
      } catch (error) {
        clearInterval(pollingTimer);
        pollingTimer = null;
        showStatus("오류", 100, error.message);
        setBusy(false);
      }
    }, 1200);
  }

  async function loadTasks() {
    try {
      const response = await fetch("tasks");
      const data = await response.json();
      const tasks = Array.isArray(data.tasks) ? data.tasks : [];
      const active = tasks.filter((task) => ["queued", "processing"].includes(task.status));
      const completed = tasks.filter((task) => !["queued", "processing"].includes(task.status));

      renderActive(active);
      renderHistory(
        completed.filter((task) => {
          if (!searchQuery) return true;
          const text = `${task.topic || ""} ${task.grade || ""} ${task.result?.title || ""}`.toLowerCase();
          return text.includes(searchQuery);
        })
      );
    } catch (error) {
      tasksList.innerHTML = `<p class="empty">목록을 불러오지 못했습니다. ${escapeHtml(error.message)}</p>`;
    }
  }

  function renderActive(tasks) {
    activeSection.classList.toggle("hidden", tasks.length === 0);
    activeList.innerHTML = tasks.map(renderTaskCard).join("");
  }

  function renderHistory(tasks) {
    if (!tasks.length) {
      tasksList.innerHTML = `<p class="empty">저장된 문서가 없습니다.</p>`;
      return;
    }
    tasksList.innerHTML = tasks.map(renderTaskCard).join("");
  }

  function renderTaskCard(task) {
    const title = task.result?.title || task.topic || "제목 없음";
    const createdAt = formatDate(task.created_at);
    const statusTextValue = statusLabel(task.status);
    const actions =
      task.status === "completed"
        ? `
          <button type="button" onclick="window.open('view/${task.task_id}', '_blank')">
            <span class="btn-icon" aria-hidden="true">↗</span>
            열기
          </button>
          <button type="button" onclick="window.location.href='download/${task.task_id}'">
            <span class="btn-icon" aria-hidden="true">↓</span>
            다운로드
          </button>
          <button type="button" class="danger" onclick="deleteTask('${task.task_id}')">
            <span class="btn-icon" aria-hidden="true">×</span>
            삭제
          </button>
        `
        : `<span class="progress-chip">${Number(task.percent || 0)}%</span>`;

    return `
      <article class="task-card">
        <div>
          <div class="task-meta">
            <span>${escapeHtml(task.grade || "")}</span>
            <span>${escapeHtml(statusTextValue)}</span>
            <span>${escapeHtml(createdAt)}</span>
          </div>
          <h3>${escapeHtml(title)}</h3>
          <p>${escapeHtml(task.topic || "")}</p>
          ${task.error ? `<p class="error-text">${escapeHtml(task.error)}</p>` : ""}
        </div>
        <div class="task-actions">${actions}</div>
      </article>
    `;
  }

  function statusLabel(status) {
    return {
      queued: "대기",
      processing: "생성 중",
      completed: "완료",
      failed: "실패",
    }[status] || status || "";
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

  window.deleteTask = async (taskId) => {
    if (!confirm("저장된 HTML과 기록을 삭제할까요?")) return;
    const response = await fetch(`delete/${taskId}`, { method: "POST" });
    const data = await response.json();
    if (!data.success) alert(data.error || "삭제에 실패했습니다.");
    loadTasks();
  };

  loadTasks();
  setInterval(loadTasks, 3000);
});
