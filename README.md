# SVPX Community — SA-MP Modding Platform

![Version](https://img.shields.io/badge/version-1.0.0-red)
![Flask](https://img.shields.io/badge/Flask-3.1.3-black)

**SVPX Community** is a professional full-stack SA-MP gaming website focused on SA-MP downloads and tools. Built with Python Flask and SQLite, featuring a dark cyberpunk hacker aesthetic with red neon accents.

## Features

- **Homepage** with animated hero section and server info widget
- **Download Center** with 9 categories: ASI, CLEO, MoonLoader, ModLoader, SA-MP Tools, HUDs, Maps, Effects, Misc
- **Search System** with category filtering
- **File Cards** with image, title, description, upload date, download counter
- **News/Updates** section
- **Server/Community info widget** with online status, player count, uptime
- **Admin Panel** with sidebar navigation, dashboard statistics, full CRUD
- **File Upload** directly from admin dashboard (50MB limit)
- **Discord Button** linked to https://discord.gg/zp4qXWwWw
- **Live Hacker Console** animation overlay
- **Loading Screen** with fake terminal boot sequence
- **Animated Particles** background
- **Responsive** design for mobile and desktop

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3 + Flask |
| Database | SQLite (WAL mode) |
| Frontend | HTML5, CSS3, JavaScript |
| CSS Framework | Bootstrap 5.3 |
| Icons | Font Awesome 6 |
| Fonts | Orbitron, JetBrains Mono, Chakra Petch, Inter, Rajdhani |

## Categories

- ASI
- CLEO
- MoonLoader
- ModLoader
- SA-MP Tools
- HUDs
- Maps
- Effects
- Misc

## Project Structure

```
SVPX-Community/
├── app.py                 # Flask application
├── database.py            # SQLite models
├── requirements.txt       # Dependencies
├── README.md              # This file
├── svpx.db                # SQLite database (auto-created)
├── uploads/               # File uploads
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
└── templates/
    ├── base.html
    ├── index.html
    ├── downloads.html
    ├── news.html
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── downloads.html
        ├── edit_download.html
        ├── categories.html
        ├── news.html
        └── settings.html
```

## Installation

```bash
cd SVPX-Community
pip install -r requirements.txt
python app.py
```

Server starts at **http://0.0.0.0:5000**

## Admin Credentials

| Field | Value |
|-------|-------|
| URL | `http://localhost:5000/admin/login` |
| Username | `admin` |
| Password | `svpx_admin_2026` |

## Security

- Passwords hashed with Werkzeug
- Session-based admin authentication
- File upload validation
- Secure file naming with MD5 + timestamp
