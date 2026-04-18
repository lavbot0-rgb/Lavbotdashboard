# Lavbot Bullpen Dashboard

A lightweight iOS-style dashboard for the Bullpen paper-trading bot.

## Local refresh

From the workspace root:

```bash
python3 projects/bullpen-dashboard/build_dashboard_data.py
```

This reads the live Bullpen bot state from:

- `projects/bullpen-bot/state/*.json`
- `projects/bullpen-bot/reports/*.txt`

and writes:

- `projects/bullpen-dashboard/dashboard-data.json`

## GitHub Pages

This repo is static-site friendly.

Recommended setup:

- Branch: `main`
- Folder: `/ (root)`

Then GitHub Pages can serve `index.html` directly.
