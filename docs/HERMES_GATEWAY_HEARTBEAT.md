# Hermes Gateway External Heartbeat

This heartbeat detects a stopped Hermes gateway, failed scheduler, offline VPS, or lost VPS
network connection. The alert must come from an external service because Hermes cannot report
its own outage.

## External Check

Create one check in an external dead-man monitoring service. Healthchecks.io is a compatible
option documented at `https://healthchecks.io/docs/monitoring_cron_jobs/`.

- Check name: `paper-bot-hermes-gateway`
- Period: `5 minutes`
- Grace time: `10 minutes`
- Alerts: enable at least one destination independent of Hermes, such as Healthchecks.io's
  Telegram integration and email

Copy the generated private HTTPS ping URL. Do not paste it into Codex, Hermes prompts, Git,
Telegram, Discord, logs, screenshots, or command arguments.

## Private Configuration

From an interactive VPS terminal in `C:\dev\paper-trading-bot`, run:

```powershell
.venv\Scripts\python.exe scripts\configure_gateway_heartbeat.py
```

Paste the URL only into the hidden prompt. The configurator validates HTTPS and stores the URL
in ignored `.env.gateway-heartbeat`. It never displays the URL. The sender also supports a
process-level `PAPER_BOT_HEARTBEAT_URL` environment variable, which takes precedence.

Send one manual test ping:

```powershell
.venv\Scripts\python.exe scripts\send_gateway_heartbeat.py
```

Success returns exit code zero with no output on success. Confirm the external check records the
ping before creating the Hermes job. A configuration or network failure returns nonzero and
prints only a generic status without the private URL.

## Hermes Job

- Job name: `paper-bot-gateway-heartbeat`
- Enabled: `true`
- Cron expression: `*/5 * * * *`
- Global scheduler timezone: keep `Europe/London`
- Working directory: `C:\dev\paper-trading-bot`
- Mode: script-only / no-agent
- Enabled toolsets: `terminal`
- Delivery: disable routine delivery if Hermes supports it; otherwise keep Telegram delivery and
  verify the no-output success path does not produce routine chat messages
- Command:

```powershell
.venv\Scripts\python.exe scripts\send_gateway_heartbeat.py
```

This job must contain only that command. It must not run Git, tests, package installation, bot
commands, trading commands, config display, or retries. It must not print or deliver the private
heartbeat URL. Do not modify the existing monitoring or autonomous paper jobs.

With a five-minute period and ten-minute grace, the external service should alert roughly 15
minutes after the last successful ping. A missing ping can mean Hermes stopped, the VPS stopped,
scheduling failed, the network failed, or the heartbeat endpoint could not be reached. Investigate
before assuming the trading bot itself failed.
