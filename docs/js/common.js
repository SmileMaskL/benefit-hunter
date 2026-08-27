/* salary-calculator의 js/common.js에서 다크모드·공유하기 로직만 그대로 가져왔다.
   완전히 브라우저 안에서만 동작하며 서버/외부 서비스를 쓰지 않는다. */

function toggleTheme() {
  const root = document.documentElement;
  const isDark = root.getAttribute("data-theme") === "dark";
  if (isDark) {
    root.removeAttribute("data-theme");
    try { localStorage.setItem("theme", "light"); } catch (e) {}
  } else {
    root.setAttribute("data-theme", "dark");
    try { localStorage.setItem("theme", "dark"); } catch (e) {}
  }
  updateThemeToggleIcon();
}

function updateThemeToggleIcon() {
  const btn = document.getElementById("themeToggle");
  if (!btn) return;
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  btn.textContent = isDark ? "☀️" : "🌙";
}

document.addEventListener("DOMContentLoaded", updateThemeToggleIcon);

function shareCurrentPage(message) {
  const url = window.location.href;
  const shareData = { title: document.title, text: message || document.title, url };
  if (navigator.share) {
    navigator.share(shareData).catch(function () {});
    return;
  }
  try {
    navigator.clipboard.writeText(url);
    alert("링크를 복사했습니다. 원하는 곳에 붙여넣어 공유하세요!");
  } catch (e) {
    prompt("아래 링크를 복사해서 공유하세요:", url);
  }
}
