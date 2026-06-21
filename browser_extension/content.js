chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "BOSSPILOT_COLLECT_PAGE") {
    return false;
  }

  sendResponse({
    pageTitle: document.title || "",
    pageUrl: window.location.href || "",
    rawText: document.body ? document.body.innerText || "" : ""
  });

  return true;
});

let lastUrl = window.location.href;
let notifyTimer = null;

function notifyPageChanged(reason) {
  if (notifyTimer) {
    clearTimeout(notifyTimer);
  }

  notifyTimer = setTimeout(() => {
    chrome.runtime.sendMessage({
      type: "BOSSPILOT_PAGE_CHANGED",
      reason,
      pageUrl: window.location.href
    });
  }, 1500);
}

setInterval(() => {
  if (window.location.href !== lastUrl) {
    lastUrl = window.location.href;
    notifyPageChanged("url_changed");
  }
}, 1500);

const observer = new MutationObserver(() => {
  notifyPageChanged("content_changed");
});

if (document.body) {
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });
}

window.addEventListener("load", () => notifyPageChanged("page_loaded"));
