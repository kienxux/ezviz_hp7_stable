# Install this fork with HACS

This is a fork of [Bobsilvio/ezviz_hp7](https://github.com/Bobsilvio/ezviz_hp7) with one change: it keeps **one stable EZVIZ terminal**.

## Why this fork exists

EZVIZ allows only 10 terminals per account. The original integration derived its terminal ID (featureCode) from the MAC address of the machine. In Docker the container MAC changes with its IP, so every restart or recreate could register a new terminal until the limit was reached and login failed.

This fork generates the ID once and stores it in `/config/.storage/ezviz_hp7_feature_code`. Existing installs adopt the ID they already use, so updating does not add a terminal. This repository is maintained on its own and may develop in its own direction, so it can differ from the original project over time.

## Before you start

Make a Home Assistant backup (Settings > System > Backups). You need Home Assistant 2025.9.0 or newer and HACS installed.

## Install (new users)

**Step 1.** Open HACS > three-dot menu > Custom repositories.

**Step 2.** Repository: `https://github.com/kienxux/ezviz_hp7_stable`, Type: **Integration**, then Add.

**Step 3.** Search for **Ezviz Hp7** in HACS and click Download.

**Step 4.** Restart Home Assistant completely (a reload is not enough).

**Step 5.** Settings > Devices & Services > Add Integration > EZVIZ HP7 / CP7.

## Switch from the original repository

The fork uses the same integration name as the original, so only one of them can be installed.

**Step 1.** Make a backup first.

**Step 2.** HACS > Ezviz Hp7 (original) > three-dot menu > Remove. Your account settings stay stored in Home Assistant.

**Step 3.** Add the fork as a custom repository and download it (Install steps 1 to 3 above).

**Step 4.** Restart Home Assistant completely.

**Step 5.** Check that the integration loads and the entities are back. No new terminal should appear in the EZVIZ app under User > Login settings > Manage terminals.

## Check that it works

The file `/config/.storage/ezviz_hp7_feature_code` exists and contains 32 hex characters. It stays the same after restarts, container recreates and IP changes. The Home Assistant log shows `EZVIZ HP7: persisted feature code` once, on the first start.

## Good to know

Old terminals registered by earlier versions stay in your EZVIZ account. Remove the unused ones once in the EZVIZ app.

Delete the file above only if you want a new terminal ID (one new terminal is registered).

When moving to another machine, restore a backup (it contains the file) or set the environment variable `EZVIZ_HP7_FEATURE_CODE` to the old 32-character value.

This fork has no numbered releases. HACS installs the latest commit of the main branch and shows its commit ID as the version.

To get upstream changes, use Sync fork on the GitHub page of this repository.

## Go back to the original

Remove this repository in HACS, add `https://github.com/Bobsilvio/ezviz_hp7` as custom repository and restart Home Assistant. The stored ID file is simply ignored by the original version.

## Problems?

Open an issue on this repository with the integration version, your device model and the log lines containing `ezviz_hp7`.
