StudyBot Implementation TODOs

Top-level goal: implement the StudyBot ecosystem features incrementally. Each task below is actionable and small enough to implement, test, and review.

1. Core infra
   - [ ] Add DB schema for study logs, streaks, reminders, doubts, XP/levels (file: `utils/db.py` or `data/` JSON schema).
   - [ ] Add `/stats` Flask route to expose uptime/ping for website (file: `bot.py` + website route).

2. Pomodoro & Focus
   - [ ] Implement `/focus start <minutes>` command in `cogs/progress.py` or `cogs/study.py`.
   - [ ] Store active timers in memory or lightweight DB; emit end-of-session notifications and short motivational lines.
   - [ ] Website: add real-time display of running timers (JS polling to `/stats` or socket).

3. Study logs & streaks
   - [ ] Implement `/log` command to save study sessions into `data/study_logs.json` or DB.
   - [ ] Implement `/logs view` to show recent entries.
   - [ ] Auto-update streak on daily log; ensure timezone handling.

4. Reminders & Schedule
   - [ ] Implement `/remind` in `cogs/reminders.py` to schedule one-off and recurring reminders.
   - [ ] Support DM or channel delivery; add timezone parsing.

5. Doubt Collector
   - [ ] Implement `/doubt ask` to store doubts in `data/doubts.json`.
   - [ ] Add `cogs/announcements.py` integration for mentors to fetch unresolved doubts.

6. Leaderboard, XP & Levels
   - [ ] Add XP model and awarding rules (study time → XP).
   - [ ] Implement `/rank` and `/leaderboard` commands.

7. AI & Gemini integration (higher priority: plan and mock)
   - [ ] Create a secure config for Gemini API keys (`config.json` already exists) and add helper wrapper in `utils/gemini.py` (mock first).
   - [ ] Implement Motivational Responder and Mentor Mode using mock responses; replace with Gemini later.

8. Site analytics & reports
   - [ ] Add `analytics` route and templates to show total hours, streaks, leaderboard.
   - [ ] Implement weekly report generation task (cron or background job).

9. Voice features (defer)
   - [ ] Research speech recognition libraries for voice commands in VC (Discord voice integration is non-trivial). Defer until core features stable.

10. Tests & QA
   - [ ] Add unit tests for core commands (see `tests/` pattern). Add CI instructions to README.

Quick next steps (first 2 weeks):
 - Implement DB schema and `/log` + `/logs view` (high impact, low risk).
 - Add Pomodoro `/focus start` (visible UX improvement).
 - Add `/stats` for website ping/uptime.

Notes:
 - Use existing `data/` JSON files when possible for minimal persistence.
 - Prefer adding new cogs under `cogs/` following current naming conventions.
