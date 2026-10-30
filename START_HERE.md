# Daze of Thunder — Broadcast Kit v1.3

**One ZIP per broadcaster. Two racing modes. Zero race-by-race information entry.**

This release adds a small read-only iRacing telemetry bridge to the existing seven-scene OBS Universal Master. It is **not** Daze Broadcast AI. It never changes cameras, controls your car, transmits telemetry outside the PC, or requires logins/API keys. The local server binds exclusively to `127.0.0.1`.

## For team members (download the **Windows ZIP** from Releases)

1. Install **OBS Studio** and **iRacing** as usual. You do not need Python or other telemetry software.
2. Download `Daze_of_Thunder_Broadcast_Kit_v1.3_Windows.zip` from the GitHub Release and **Extract All**.
3. Double-click `INSTALL_WINDOWS.cmd`. It installs assets and the bridge in `%USERPROFILE%\Videos\DazeBroadcastKitUniversal` and creates the OBS import file.
4. Double-click `%USERPROFILE%\Videos\DazeBroadcastKitUniversal\START_DAZE.cmd`. Keep the telemetry console window open when streaming.
5. Open OBS, select **Scene Collection → Import**, choose `%USERPROFILE%\Videos\DazeBroadcastKitUniversal\DAZE_OBS_MASTER_v1.3_IMPORT.json`, then select the new v1.3 scene collection. Existing v1.2 scenes remain unchanged.
6. Choose **`02 | DRIVER POV`** if racing or **`03 | BROADCAST TEAM`** if spectating. Configure **`DAZE | IRACING GAME - SET WINDOW`** for the current iRacing simulator process. Configure microphone/game audio once.
7. Enter iRacing. In a live session the overlay reads local driver names, positions, lap and flags automatically. With iRacing closed, telemetry cards disappear; the brand art remains. No fake values.
8. Make a **30-second local OBS recording** to test game, microphone, and graphics. Privately connect OBS to the official YouTube channel only after the recording works.

**Every broadcast:** Start iRacing, run `START_DAZE.cmd`, select the appropriate OBS scene, check meters, then go live. No race/track/date/driver form.

## Two racing modes

**Driver POV:** Daze branding, player car number/name, the player's official position when available, actual best lap/lap progress, and live flag. If an item is unavailable it is hidden.

**Broadcast Team:** Daze branding, track/session name if supplied by iRacing, live running order (top 10), iRacing focus-camera driver, lap progress and session flag. During practice/qualifying where official race positions are unavailable, it can show a **FASTEST LAPS** table based on supplied telemetry instead, clearly labeled to avoid passing it off as race standings. A blank/no telemetry panel is intentional in menu/garage or when disconnected.

**Note:** Camera focus uses `CamCarIdx`. Some session/camera combinations do not expose this field; in that case it falls back to the local player's car if available. Some spectator setups may not provide an appropriate focus card. No camera control is attempted.

In Broadcast Team, hide iRacing's built-in *Standings* widget if both tables overlap; the OBS package now renders the running order on its own.

## Local endpoints (on each member's computer)

- Driver overlay: `http://127.0.0.1:8766/driver`
- Broadcast overlay: `http://127.0.0.1:8766/broadcast`
- Current session snapshot: `http://127.0.0.1:8766/api/state`
- Connection indicator: `http://127.0.0.1:8766/health`

These links are used **locally** by OBS and do not point to GitHub or a public server.

## If the overlay is blank or the OBS Browser Source says the site cannot be reached

- Start `START_DAZE.cmd` first and leave its console window open. Confirm the local `/health` URL loads in your normal web browser.
- Enter an iRacing practice or race session. The bridge only shows data actually received from the simulator.
- Verify the OBS Browser Source URL and dimensions: 1920 × 1080. Right-click source → Refresh cache of current page.
- In OBS, confirm Game Capture is **below** the telemetry Browser Source in the Sources panel.
- If an older OBS scene is still active, change to `DAZE OF THUNDER - BROADCAST KIT v1.3` or import the v1.3 file. v1.2 local HTML graphics will not automatically turn into telemetry sources.
- Never launch with `--demo` for a public broadcast; it shows simulated data and an obvious red demo banner.

## Developer / maintainer (GitHub Actions builds the executable)

This source repository **does not contain a precompiled Windows executable**. To produce the easy one-ZIP team package:

1. Create a GitHub repository (for example `daze-broadcast-kit`) and upload the contents of **this source ZIP**, preserving `.github/workflows/build-windows.yml`.
2. Push to `main` or click **Actions → Build Daze Broadcast Kit for Windows → Run workflow**.
3. After the build passes, download the **Daze-Broadcast-Kit-v1.3-Windows** artifact from that run. That artifact contains the complete Windows ZIP with `DazeTelemetry.exe`.
4. For a stable team download, create and push a tag like `v1.3.0`. The tag build publishes the Windows ZIP in **GitHub Releases**, if workflow permissions allow releases. Team members then download the Release ZIP.
5. Test on a real Windows iRacing session and a spectator session *before* announcing a production release. Windows and iRacing SDK behavior cannot be validated in this Linux development environment.

Run locally for development (Python 3.12 or later; only maintainers need it):

```shell
python -m pip install pyirsdk==1.3.6 PyYAML
python launch.py --demo
```

For live mode, on Windows with iRacing installed, use `python launch.py` instead of `--demo`. To run automated tests: `python -m unittest discover -s tests -v`.

## Security / distribution

- No YouTube keys, OAuth tokens, Discord credentials, race data, or telemetry recordings ship in the ZIP.
- No custom server/Oracle/Cloudflare required; GitHub stores versions and releases, **not** live telemetry.
- The bridge exposes a small read-only JSON endpoint on the PC's loopback interface. It does not bind to your LAN/Wi-Fi IP.
- Do not ship a demo screenshot or a sample stream as a real race result. The `--demo` mode is watermarked and never started by `START_DAZE.cmd`.
- `DazeTelemetry.exe` is an unsigned build when created by GitHub Actions; Windows SmartScreen may prompt for confirmation. Only distribute artifacts built from your trusted repository.

## Attribution

iRacing shared-memory access is implemented through [pyirsdk](https://github.com/kutu/pyirsdk) by kutu. OBS Browser Source is part of the official OBS Studio installation. Team graphics use your previously provided Daze of Thunder assets. This is an unofficial community tool, not affiliated with iRacing or OBS.
