# waw-calendars — Home Assistant add-on

Runs the full pipeline (fetch + generate) from your home network, so the Wola
source works too (its site 403s cloud/datacenter IPs). Results are committed to
the repo `data` branch exactly as the GitHub workflow would.

It is a **one-shot** add-on: each start runs the pipeline once and exits. Trigger
it on a schedule from an automation (see below).

## Install (HA OS / Supervised)

1. Copy this `waw_calendars/` folder into your Home Assistant `/addons` share
   (e.g. via the Samba or SSH add-on). The path becomes
   `/addons/waw_calendars/`.
2. Settings → Add-ons → Add-on Store → ⋮ → **Check for updates**, then open
   **Local add-ons** and install *waw-calendars*.

## Deploy key (write access to the repo)

The add-on pushes to the `data` branch over SSH.

1. Generate a key (no passphrase):
   ```bash
   ssh-keygen -t ed25519 -f deploy_key -C "waw-calendars-ha" -N ""
   ```
2. Add `deploy_key.pub` to the GitHub repo: Settings → Deploy keys → *Add deploy
   key* → **Allow write access**.
3. Put the private key on the HA host at `/config/waw_calendars/deploy_key`
   (the default `deploy_key_path`). Keep it private.

## Options

| option            | default                                   | meaning                                   |
|-------------------|-------------------------------------------|-------------------------------------------|
| `repo_url`        | `git@github.com:mik-laj/waw-calendars.git`| SSH remote to clone/push                  |
| `data_branch`     | `data`                                    | branch that stores YAML + `.ics`          |
| `deploy_key_path` | `/config/waw_calendars/deploy_key`        | private SSH key file                      |
| `days`            | `14`                                      | generation window length                  |
| `throttle`        | `0.5`                                     | min seconds between HTTP requests         |
| `git_user_name`   | `home-assistant`                          | commit author name                        |
| `git_user_email`  | `ha@localhost`                            | commit author email                       |

## Schedule it

Add an automation that starts the add-on on a schedule (slug for a local add-on
is `local_waw_calendars`):

```yaml
automation:
  - alias: "waw-calendars refresh"
    trigger:
      - platform: time_pattern
        hours: "/6"          # every 6 hours
    action:
      - service: hassio.addon_start
        data:
          addon: local_waw_calendars
```

Watch progress under the add-on's **Log** tab. See `docs/home-assistant.md` in
the repo for more detail and troubleshooting.
