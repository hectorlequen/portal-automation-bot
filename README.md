# Web Portal Automation Bot

A bot that logs into a website, retrieves a document, and alerts you if something goes wrong — no human intervention required.

## The problem

Many businesses have a recurring manual task: log into a portal (supplier extranet, admin platform, client area...), navigate to a document, download it. Every week or month, someone has to remember to do it, log in, and get it done — time taken away from higher-value work.

**Why isn't this already automated with a tool like Zapier or Make?** Because those tools only work with APIs. The vast majority of web portals (supplier extranets, administrative platforms, client areas) don't expose any. Automating this kind of task requires driving a real browser, the way a human would — something only a developer can build.

## What this bot does

- Automatically logs into a portal with credentials
- Navigates to the target document and downloads it
- Verifies each step completed successfully before moving on
- Automatically retries when the site is temporarily slow
- Alerts you immediately (Slack) if login fails, instead of discovering the problem weeks later
- Keeps a detailed log of every run, available for review at any time

## Reliability

This project includes an automated test suite that verifies the bot's behavior across different scenarios (successful login, incorrect credentials, temporarily unavailable site, interrupted download) — to ensure stable behavior in production, not just "it works on my machine."

## Demo

The repository includes a reproducible demo portal: a login page, a protected area, and a document to download — so the bot can be observed in action without depending on a third-party site.

The bot can run with or without the browser window visible, useful for a live demo as well as unattended background execution.

## Deployment

The bot is packaged with Docker, ensuring consistent behavior across environments — development, production server, or a client's machine.

## Adapting to a new portal

Configuration (site address, elements to target) is fully separated from the code. Adapting the bot to a new portal requires no changes to the program itself — a real advantage for fast onboarding of a new client.

## Contact

Built by Hector Lequen — available for custom automation projects.