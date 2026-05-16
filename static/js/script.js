document.addEventListener("DOMContentLoaded", function () {
    initLoadingScreen();
    initParticles();
    initNavbarScroll();
    initConsoleLogs();
    initSmoothScroll();
    initCounterAnimation();
    initDiscordWidget();
    initDevDate();
});

function initLoadingScreen() {
    const ls = document.getElementById("loading-screen");
    if (!ls) return;
    setTimeout(function () {
        ls.classList.add("hidden");
        document.body.style.overflow = "visible";
    }, 3200);
}

function initParticles() {
    const canvas = document.getElementById("particles-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let particles = [];
    let mouseX = 0, mouseY = 0;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.6;
            this.speedY = (Math.random() - 0.5) * 0.6;
            this.opacity = Math.random() * 0.4 + 0.1;
            this.hue = Math.random() < 0.3 ? 0 : 10;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x > canvas.width) this.x = 0;
            if (this.x < 0) this.x = canvas.width;
            if (this.y > canvas.height) this.y = 0;
            if (this.y < 0) this.y = canvas.height;
            const dx = mouseX - this.x;
            const dy = mouseY - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 120) {
                this.x -= dx * 0.008;
                this.y -= dy * 0.008;
            }
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255,0,51, ${this.opacity})`;
            ctx.fill();
        }
    }

    const count = Math.min(Math.floor(canvas.width * canvas.height / 7000), 120);
    for (let i = 0; i < count; i++) particles.push(new Particle());

    function connect() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 140) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(255,0,51, ${0.04 * (1 - dist / 140)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach((p) => { p.update(); p.draw(); });
        connect();
        requestAnimationFrame(animate);
    }
    animate();

    document.addEventListener("mousemove", (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });
}

function initNavbarScroll() {
    const navbar = document.querySelector(".navbar");
    if (!navbar) return;
    window.addEventListener("scroll", () => {
        navbar.classList.toggle("scrolled", window.scrollY > 50);
    });
}

const consoleMessages = [
    "[SVPX] Initializing security protocols...",
    "[NETWORK] Establishing encrypted tunnel on port 7777...",
    "[AUTH] Handshake complete. Session: 0x7F4D3A",
    "[CACHE] Loading asset database... 47 entries indexed",
    "[MODULE] asi_loader.dll injected @ 0x4FF800",
    "[PROXY] Routing through node-frankfurt-01... OK",
    "[STREAM] Downloading vehicle: infernus.txd",
    "[MEMORY] Allocated 0x4FF800 bytes for hook engine",
    "[CORE] Anti-cheat signature scan: CLEAN",
    "[SYSTEM] Server heartbeat: 32ms latency",
    "[NETWORK] Peer connected: 192.168.x.x:54321",
    "[RENDER] FPS: 92 | Draw distance: 500m",
    "[AUDIO] Audio stream: GTA San Andreas Radio",
    "[SVPX] All systems operational.",
];

function initConsoleLogs() {
    const overlay = document.getElementById("console-overlay");
    if (!overlay) return;
    let index = 0;
    function showLog() {
        if (index >= consoleMessages.length) index = 0;
        const log = document.createElement("div");
        log.className = "console-log";
        log.textContent = "> " + consoleMessages[index];
        overlay.appendChild(log);
        setTimeout(() => { if (log.parentNode) log.remove(); }, 5000);
        index++;
    }
    showLog();
    setInterval(showLog, 3500 + Math.random() * 4000);
}

function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
        a.addEventListener("click", function (e) {
            e.preventDefault();
            const t = document.querySelector(this.getAttribute("href"));
            if (t) t.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });
}

function initCounterAnimation() {
    const counters = document.querySelectorAll(".counter-number");
    if (!counters.length) return;
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target, parseInt(entry.target.dataset.target) || 0);
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.5 }
    );
    counters.forEach((c) => observer.observe(c));
}

function animateCounter(el, target) {
    let current = 0;
    const step = Math.ceil(target / 60);
    const interval = setInterval(() => {
        current += step;
        if (current >= target) { current = target; clearInterval(interval); }
        el.textContent = current;
    }, 25);
}

function initDiscordWidget() {
    const nameEl = document.getElementById("discord-name");
    const iconEl = document.getElementById("discord-icon");
    const onlineEl = document.getElementById("discord-online");
    const membersEl = document.getElementById("discord-members");
    const descEl = document.getElementById("discord-description");
    const statusLabel = document.getElementById("discord-status-label");
    const dotEl = document.getElementById("discord-dot");
    const btnEl = document.getElementById("discord-join-btn");
    if (!nameEl) return;

    function fetchDiscord() {
        fetch("/discord/status")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) { statusLabel.textContent = "unreachable"; dotEl.className = "status-dot status-offline"; return; }
                nameEl.textContent = data.name;
                if (iconEl) iconEl.src = data.icon || "https://cdn.discordapp.com/embed/avatars/0.png";
                if (onlineEl) onlineEl.textContent = data.online;
                if (membersEl) membersEl.textContent = data.members;
                if (descEl && data.description) descEl.textContent = data.description;
                if (statusLabel) statusLabel.textContent = "● online";
                if (dotEl) dotEl.className = "status-dot status-online";
                if (btnEl) btnEl.href = data.invite;
            })
            .catch(function () {
                if (statusLabel) statusLabel.textContent = "unreachable";
                if (dotEl) dotEl.className = "status-dot status-offline";
            });
    }

    fetchDiscord();
    setInterval(fetchDiscord, 60000);
}

function initDevDate() {
    var el = document.getElementById("dev-date");
    if (!el) return;
    function update() {
        var d = new Date();
        var y = d.getFullYear();
        var m = ("0"+(d.getMonth()+1)).slice(-2);
        var day = ("0"+d.getDate()).slice(-2);
        el.textContent = y + "-" + m + "-" + day;
    }
    update();
    setInterval(update, 86400000);
}
