const BOSSPILOT_URL = "http://localhost:8501";
// 上线后可改为：
// const BOSSPILOT_URL = "https://bosspilot-yij7.streamlit.app";

const BOSSPILOT_RECEIVER_URL = "http://127.0.0.1:8765/api/import-session";
const MAX_TEXT_LENGTH = 10000;

const statusEl = document.getElementById("status");
const sendButton = document.getElementById("sendButton");
const monitorStatusEl = document.getElementById("monitorStatus");
const pageCountEl = document.getElementById("pageCount");
const jobCountEl = document.getElementById("jobCount");
const startMonitorButton = document.getElementById("startMonitorButton");
const endUploadButton = document.getElementById("endUploadButton");
const refreshCountButton = document.getElementById("refreshCountButton");
const clearSessionButton = document.getElementById("clearSessionButton");

function setStatus(text) {
  statusEl.textContent = text;
}

function sendRuntimeMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      const error = chrome.runtime.lastError;
      if (error) {
        reject(new Error(error.message));
      } else {
        resolve(response || {});
      }
    });
  });
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs && tabs[0] ? tabs[0] : null;
}

function buildBossPilotUrl(pageData) {
  const params = new URLSearchParams({
    source: "extension",
    page_title: pageData.pageTitle || "",
    page_url: pageData.pageUrl || "",
    raw_text: (pageData.rawText || "").slice(0, MAX_TEXT_LENGTH)
  });
  return `${BOSSPILOT_URL}/?${params.toString()}`;
}

async function collectPageData(tab) {
  try {
    return await chrome.tabs.sendMessage(tab.id, { type: "BOSSPILOT_COLLECT_PAGE" });
  } catch (error) {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => ({
        pageTitle: document.title || "",
        pageUrl: window.location.href || "",
        rawText: document.body ? document.body.innerText || "" : ""
      })
    });
    return results && results[0] ? results[0].result : null;
  }
}

function renderMonitorState(state) {
  monitorStatusEl.textContent = state.status || "未开始";
  pageCountEl.textContent = state.pageCount || 0;
  jobCountEl.textContent = state.jobCount || 0;
}

async function refreshMonitorState() {
  const state = await sendRuntimeMessage({ type: "BOSSPILOT_GET_STATE" });
  renderMonitorState(state);
  return state;
}

async function uploadSession(state) {
  if (!state.pages || state.pages.length === 0) {
    setStatus("本次会话还没有采集到 Boss 页面。");
    return;
  }

  const payload = {
    session_id: state.sessionId || `boss_session_${Date.now()}`,
    created_at: state.createdAt || new Date().toISOString(),
    source: "boss_chrome_extension",
    pages: state.pages
  };

  const response = await fetch(BOSSPILOT_RECEIVER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const responseText = await response.text();
  if (!response.ok) {
    throw new Error(`上传失败：${response.status} ${responseText.slice(0, 300)}`);
  }

  setStatus("已上传到 BossPilot，请查看分析结果。");
}

sendButton.addEventListener("click", async () => {
  sendButton.disabled = true;
  setStatus("正在读取当前页面...");

  try {
    const tab = await getActiveTab();
    if (!tab || !tab.id) {
      setStatus("未找到当前标签页。");
      return;
    }

    const pageData = await collectPageData(tab);
    if (!pageData || !pageData.rawText) {
      setStatus("未读取到页面文字，请确认当前页面为 Boss 直聘岗位详情页。");
      return;
    }

    const targetUrl = buildBossPilotUrl(pageData);
    await chrome.tabs.create({ url: targetUrl });
    setStatus("已发送到 BossPilot，请在新页面查看分析结果。");
  } catch (error) {
    setStatus(`发送失败：${error.message || error}`);
  } finally {
    sendButton.disabled = false;
  }
});

startMonitorButton.addEventListener("click", async () => {
  startMonitorButton.disabled = true;
  setStatus("监控已开始，请正常浏览 Boss 直聘页面。");

  try {
    let state = await sendRuntimeMessage({ type: "BOSSPILOT_START_MONITOR" });
    renderMonitorState(state);
    state = await sendRuntimeMessage({ type: "BOSSPILOT_CAPTURE_ACTIVE_TAB" });
    renderMonitorState(state);
  } catch (error) {
    setStatus(`开始监控失败：${error.message || error}`);
  } finally {
    startMonitorButton.disabled = false;
  }
});

endUploadButton.addEventListener("click", async () => {
  endUploadButton.disabled = true;
  setStatus("正在结束监控并上传本次会话...");

  try {
    let state = await sendRuntimeMessage({ type: "BOSSPILOT_STOP_MONITOR" });
    renderMonitorState(state);
    await uploadSession(state);
  } catch (error) {
    setStatus(`上传失败：${error.message || error}`);
  } finally {
    endUploadButton.disabled = false;
  }
});

refreshCountButton.addEventListener("click", async () => {
  try {
    const state = await refreshMonitorState();
    setStatus(`已采集页面数：${state.pageCount || 0}，已采集岗位数：${state.jobCount || 0}`);
  } catch (error) {
    setStatus(`读取数量失败：${error.message || error}`);
  }
});

clearSessionButton.addEventListener("click", async () => {
  clearSessionButton.disabled = true;
  setStatus("正在清空本次记录...");

  try {
    const state = await sendRuntimeMessage({ type: "BOSSPILOT_CLEAR_SESSION" });
    renderMonitorState(state);
    setStatus("本次会话记录已清空。");
  } catch (error) {
    setStatus(`清空失败：${error.message || error}`);
  } finally {
    clearSessionButton.disabled = false;
  }
});

refreshMonitorState().catch((error) => {
  setStatus(`读取监控状态失败：${error.message || error}`);
});
