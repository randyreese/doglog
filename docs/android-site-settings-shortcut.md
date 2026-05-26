# Android Chrome Site Settings Shortcut

## What this is

When you install a PWA (like Dog Log or Grow) from Chrome on Android, Chrome sometimes places a second icon on your home screen alongside the app icon. It looks like a gear with a small square — labeled "Site sett..." It's a shortcut directly to Chrome's Site Settings page for the app's origin (`https://mint.local`). It's a Chrome-generated companion, not something the app creates.

## Why it matters

PWAs store data locally on the phone — event history, config, offline queues, the backend URL — all inside Chrome's storage for `https://mint.local`. If the app gets into a bad state (stale config, corrupted cache, wrong backend URL), the fastest way to reset it is to clear that stored data. The Site Settings shortcut is the quickest path to doing that.

## What you can do from Site Settings

- **Delete data & reset permissions** — wipes all local storage for `mint.local`: Dexie IndexedDB (local events, health records, meal logs), localStorage (backend URL, config cache, last synced timestamp). After this the app opens on the ConnectPage and you re-enter the backend URL.
- **Notifications** — shows which app (Dog Log or Grow) manages notifications for the origin.
- **Stored data size** — shows how much space the PWA is using (typically 2–5 MB for normal use).

## When you'd use it

- The app is stuck, showing wrong data, or not connecting after a backend URL change
- You want a clean reinstall without uninstalling the PWA
- Debugging an issue where stale cached config might be the cause
- The "Erase all data" option in the hamburger menu is the in-app equivalent — use whichever is more convenient

## How to reach Site Settings without the shortcut

If the companion icon isn't on your home screen:
1. Open Chrome
2. Tap the three-dot menu → Settings → Site settings → All sites
3. Find `mint.local` in the list and tap it

Or long-press the Dog Log icon on the home screen — "Site settings" sometimes appears in the pop-up menu directly (as seen during the 2026-05-26 reinstall).

## Gotchas

- **Both apps share the origin** (`https://mint.local`), so "Delete data & reset permissions" clears storage for Dog Log *and* Grow simultaneously. There's no way to clear one without the other from this screen.
- The companion shortcut doesn't always appear on a fresh install. It may take one full navigation to the app before Chrome adds it.
- Clearing data doesn't uninstall the PWA — the icon stays, but the app opens to ConnectPage on next launch.
