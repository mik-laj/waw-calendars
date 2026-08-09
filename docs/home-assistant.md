# Running the pipeline from Home Assistant

The Wola source (`wola.um.warszawa.pl`) returns 403 to cloud/datacenter IPs, so
it cannot be fetched from GitHub-hosted runners. Running the pipeline from a home
network (e.g. an Intel NUC running Home Assistant, on a Polish/residential IP)
fixes this — and the other two sources work there as well. So the home runner
does **everything**, and the GitHub Actions workflow is kept only as a manual
fallback (its schedule is disabled).

The runner is packaged as a **local Home Assistant add-on** in
[`addons/waw_calendars/`](../addons/waw_calendars/). It is a one-shot container:
each start runs fetch + generate once and commits the results to the `data`
branch, then exits. An automation starts it on a schedule.

## Architecture

```
  HA automation (time_pattern)                         GitHub
        │ hassio.addon_start                          ┌──────────────┐
        ▼                                             │ data branch  │
  waw_calendars add-on (NUC, PL IP)  ── git push ───▶ │ events/*.yaml│
   fetch.sh → events/*.yaml                           │ calendars/*  │
   generate.sh → calendars/*.ics                      └──────────────┘
                                                             │ raw URL
                                                             ▼
                                                   calendar subscription
```

## Setup

1. **Deploy key** — see the add-on README. Generate an ed25519 key, add the
   public half as a repo Deploy Key with *write access*, and place the private
   key at `/config/waw_calendars/deploy_key`.
2. **Install the add-on** — copy `addons/waw_calendars/` into the HA `/addons`
   share and install it from *Local add-ons*.
3. **Configure** — adjust options if needed (defaults target this repo).
4. **Automate** — add the automation below to schedule runs.

```yaml
automation:
  - alias: "waw-calendars refresh"
    trigger:
      - platform: time_pattern
        hours: "/6"
    action:
      - service: hassio.addon_start
        data:
          addon: local_waw_calendars
```

### Why `hassio.addon_start` and not `shell_command`

On HA OS/Supervised, `shell_command` runs inside the Home Assistant Core
container, which has neither the Supervisor API access nor git/Python/our code.
The Supervisor service `hassio.addon_start` is the supported way to run a
containerised job from HA, so the add-on holds the code and dependencies and HA
just triggers it.

## Verifying

- Start the add-on manually once (Add-on page → **Start**) and watch the **Log**
  tab. You should see fetch counts for `expoxxi`, `waw4free`, `wola`, then
  generate writing the `.ics` files, then two pushes to the `data` branch.
- Check the branch: the commits should be authored by your configured
  `git_user_name`, and `calendars/wola.ics` should now contain events.

## Troubleshooting

- **`deploy key not found`** — the private key is not at `deploy_key_path`.
- **`Permission denied (publickey)` on push** — the deploy key lacks write
  access, or the public key was not added to the repo.
- **`wola` still empty** — confirm the NUC's egress IP is Polish/residential
  (some ISPs/CGNAT or a VPN could route elsewhere).
- **First run is slow** — the add-on clones the repo and installs dependencies;
  subsequent runs reuse the persistent `/data/repo` checkout.
