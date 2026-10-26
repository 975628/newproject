(() => {
    const list = document.getElementById("notification-list");
    if (!list || !window.WebSocket) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/notifications/`);
    socket.addEventListener("message", (event) => {
        const data = JSON.parse(event.data);
        const item = document.createElement("div");
        item.className = "list-group-item notification-unread";
        const message = document.createElement("div");
        message.textContent = data.message;
        const time = document.createElement("div");
        time.className = "small text-secondary";
        time.textContent = "Just now";
        item.append(message, time);
        list.querySelector(".list-group")?.prepend(item);
    });
})();
