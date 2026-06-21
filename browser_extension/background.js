const STORAGE_KEYS = {
  monitoring: "bosspilotMonitoring",
  status: "bosspilotStatus",
  sessionId: "bosspilotSessionId",
  createdAt: "bosspilotCreatedAt",
  pages: "bosspilotPages",
  lastCapturedAt: "bosspilotLastCapturedAt"
};

const DEBOUNCE_MS = 10000;
const MAX_TEXT_LENGTH = 12000;

function storageGet(keys) {
  return new Promise((resolve) => chrome.storage.local.get(keys, resolve));
}

function storageSet(values) {
  return new Promise((resolve) => chrome.storage.local.set(values, resolve));
}

function isBossUrl(url) {
  try {
    const host = new URL(url).hostname;
    return host === "zhipin.com" || host.endsWith(".zhipin.com");
  } catch (error) {
    return false;
  }
}

function compactText(text) {
  return (text || "").replace(/\s+/g, " ").trim();
}

function detectPageType(pageTitle, pageUrl, rawText) {
  const text = `${pageTitle || ""} ${pageUrl || ""} ${rawText || ""}`;
  const lowerUrl = (pageUrl || "").toLowerCase();

  if (/聊天|沟通|消息|立即沟通|chat|goutong|message/.test(text) || lowerUrl.includes("chat")) {
    return "聊天页";
  }
  if (/公司介绍|公司信息|企业信息|融资|规模|工商|company|gongsi/.test(text) || lowerUrl.includes("gongsi") || lowerUrl.includes("company")) {
    return "公司页";
  }
  if (/职位描述|岗位职责|任职要求|职位详情|岗位详情|薪资|boss直聘/.test(text) || lowerUrl.includes("job_detail") || lowerUrl.includes("detail")) {
    return "岗位详情页";
  }
  if (/职位列表|推荐职位|搜索结果|筛选|query|search|joblist/.test(text) || lowerUrl.includes("joblist") || lowerUrl.includes("query") || lowerUrl.includes("search")) {
    return "岗位列表页";
  }
  return "其他";
}

function normalizePage(pageData) {
  const rawText = (pageData.rawText || "").slice(0, MAX_TEXT_LENGTH);
  const pageTitle = pageData.pageTitle || "";
  const pageUrl = pageData.pageUrl || "";

  return {
    page_title: pageTitle,
    page_url: pageUrl,
    raw_text: rawText,
    captured_at: new Date().toISOString(),
    page_type: detectPageType(pageTitle, pageUrl, rawText),
    source: "boss_chrome_extension_session"
  };
}

function isSimilarPage(pageA, pageB) {
  const titleA = compactText(pageA.page_title);
  const titleB = compactText(pageB.page_title);
  const textA = compactText(pageA.raw_text).slice(0, 300);
  const textB = compactText(pageB.raw_text).slice(0, 300);
  return titleA && titleA === titleB && textA && textA === textB;
}

async function getState() {
  const state = await storageGet([
    STORAGE_KEYS.monitoring,
    STORAGE_KEYS.status,
    STORAGE_KEYS.sessionId,
    STORAGE_KEYS.createdAt,
    STORAGE_KEYS.pages,
    STORAGE_KEYS.lastCapturedAt
  ]);
  const pages = state[STORAGE_KEYS.pages] || [];
  const jobUrls = new Set(
    pages
      .filter((page) => page.page_type === "岗位详情页")
      .map((page) => page.page_url)
      .filter(Boolean)
  );

  return {
    monitoring: Boolean(state[STORAGE_KEYS.monitoring]),
    status: state[STORAGE_KEYS.status] || "未开始",
    sessionId: state[STORAGE_KEYS.sessionId] || "",
    createdAt: state[STORAGE_KEYS.createdAt] || "",
    pages,
    lastCapturedAt: state[STORAGE_KEYS.lastCapturedAt] || {},
    pageCount: pages.length,
    jobCount: jobUrls.size
  };
}

async function startMonitor() {
  const sessionId = `boss_session_${Date.now()}`;
  const createdAt = new Date().toISOString();
  await storageSet({
    [STORAGE_KEYS.monitoring]: true,
    [STORAGE_KEYS.status]: "监控中",
    [STORAGE_KEYS.sessionId]: sessionId,
    [STORAGE_KEYS.createdAt]: createdAt,
    [STORAGE_KEYS.pages]: [],
    [STORAGE_KEYS.lastCapturedAt]: {}
  });
  return getState();
}

async function stopMonitor() {
  await storageSet({
    [STORAGE_KEYS.monitoring]: false,
    [STORAGE_KEYS.status]: "已结束"
  });
  return getState();
}

async function clearSession() {
  await storageSet({
    [STORAGE_KEYS.monitoring]: false,
    [STORAGE_KEYS.status]: "未开始",
    [STORAGE_KEYS.sessionId]: "",
    [STORAGE_KEYS.createdAt]: "",
    [STORAGE_KEYS.pages]: [],
    [STORAGE_KEYS.lastCapturedAt]: {}
  });
  return getState();
}

async function collectPageData(tabId) {
  try {
    return await chrome.tabs.sendMessage(tabId, { type: "BOSSPILOT_COLLECT_PAGE" });
  } catch (error) {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => ({
        pageTitle: document.title || "",
        pageUrl: window.location.href || "",
        rawText: document.body ? document.body.innerText || "" : ""
      })
    });
    return results && results[0] ? results[0].result : null;
  }
}

async function upsertPage(page) {
  const state = await getState();
  const pages = [...state.pages];
  const sameUrlIndex = pages.findIndex((item) => item.page_url && item.page_url === page.page_url);

  if (sameUrlIndex >= 0) {
    const existing = pages[sameUrlIndex];
    if ((page.raw_text || "").length >= (existing.raw_text || "").length) {
      pages[sameUrlIndex] = page;
    }
  } else {
    const similarIndex = pages.findIndex((item) => isSimilarPage(item, page));
    if (similarIndex >= 0) {
      const existing = pages[similarIndex];
      if ((page.raw_text || "").length >= (existing.raw_text || "").length) {
        pages[similarIndex] = page;
      }
    } else {
      pages.push(page);
    }
  }

  await storageSet({ [STORAGE_KEYS.pages]: pages });
  return getState();
}

async function captureTab(tabId, reason) {
  const state = await getState();
  if (!state.monitoring) {
    return state;
  }

  let tab;
  try {
    tab = await chrome.tabs.get(tabId);
  } catch (error) {
    return state;
  }

  if (!tab || !isBossUrl(tab.url || "")) {
    return state;
  }

  const now = Date.now();
  const lastCapturedAt = { ...state.lastCapturedAt };
  const lastTime = lastCapturedAt[tab.url] || 0;
  if (now - lastTime < DEBOUNCE_MS) {
    return state;
  }

  lastCapturedAt[tab.url] = now;
  await storageSet({ [STORAGE_KEYS.lastCapturedAt]: lastCapturedAt });

  try {
    const pageData = await collectPageData(tabId);
    if (!pageData || !pageData.rawText) {
      return getState();
    }
    return await upsertPage(normalizePage(pageData));
  } catch (error) {
    console.warn("BossPilot capture failed", reason, error);
    return getState();
  }
}

async function captureActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs || !tabs[0] || !tabs[0].id) {
    return getState();
  }
  return captureTab(tabs[0].id, "manual_active_tab");
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !message.type) {
    return false;
  }

  if (message.type === "BOSSPILOT_PAGE_CHANGED") {
    if (sender.tab && sender.tab.id) {
      captureTab(sender.tab.id, message.reason || "page_changed").then(sendResponse);
      return true;
    }
    return false;
  }

  if (message.type === "BOSSPILOT_START_MONITOR") {
    startMonitor().then(sendResponse);
    return true;
  }

  if (message.type === "BOSSPILOT_STOP_MONITOR") {
    stopMonitor().then(sendResponse);
    return true;
  }

  if (message.type === "BOSSPILOT_CLEAR_SESSION") {
    clearSession().then(sendResponse);
    return true;
  }

  if (message.type === "BOSSPILOT_GET_STATE") {
    getState().then(sendResponse);
    return true;
  }

  if (message.type === "BOSSPILOT_CAPTURE_ACTIVE_TAB") {
    captureActiveTab().then(sendResponse);
    return true;
  }

  return false;
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab && isBossUrl(tab.url || "")) {
    captureTab(tabId, "tab_complete");
  }
});

chrome.tabs.onActivated.addListener((activeInfo) => {
  captureTab(activeInfo.tabId, "tab_activated");
});
