# Security Guidelines for StudyBot

This file summarizes recommended security practices for running and developing StudyBot.

1. Secrets and `.env`
- Never commit `.env` or any file containing `DISCORD_TOKEN`, API keys, or other secrets to source control.
- Use `.gitignore` to exclude `.env` and `studybot.db` if it contains sensitive data.
- Locally, load environment variables using `python-dotenv` only in development. For production, inject secrets via your hosting provider or CI.

2. GitHub and CI
- Use GitHub Secrets for `DISCORD_TOKEN` in Actions workflows.
- Limit repository collaborators and enforce branch protection rules.

3. Permissions and roles
- When inviting the bot, grant least privilege required. Avoid `Administrator` unless necessary.
- For operations that modify nicknames or manage roles, ensure the bot's role is above the targets.

4. Dependency safety
- Pin dependencies and review `requirements.txt` for unexpected packages.
- Regularly run `pip-audit` or dependabot to detect vulnerable packages.

5. Running in production
- Run the bot in a dedicated service account and a small VM/container.
- If using SQLite, protect the file and backup securely. For higher scale, migrate to a managed DB.

6. Logging and PII
- Avoid logging user private data. Sanitize logs before sharing.
- Keep logs rotated and access-restricted.

7. Rate limits & abuse
- The bot uses Discord rate limits; avoid large bulk operations on startup.
- Use cooldowns on commands that could be abused.

8. Safe code contributions
- Review PRs for dangerous functionality (remote code execution, shell calls).
- Use automated tests for critical flows where possible.


If you want, I can generate a sample GitHub Actions workflow that uses GitHub Secrets to start an ephemeral bot or run unit tests. Let me know if you want that.
