// dashboard.js
// The server sends times in UTC. This shows them in the visitor's own time zone.

document.querySelectorAll(".local-time").forEach(function (el) {
    var date = new Date(el.getAttribute("datetime"));
    if (isNaN(date.getTime())) return;
    el.textContent = date.toLocaleString([], {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit"
    });
});