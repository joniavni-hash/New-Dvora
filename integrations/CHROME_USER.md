# Chrome (Debug Port)

## Status
Connected (requires Chrome running with debug port)

## Purpose
Browse the web as Yoni — with all logins, cookies, and sessions. No bot detection, no captchas.

## Setup
Chrome must be started with remote debugging from WSL:
```
/mnt/c/Program\ Files/Google/Chrome/Application/chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\Users\jonia\ChromeDebug" &
```

Port forwarded via socat:
```
socat TCP-LISTEN:9222,fork,reuseaddr TCP:$(ip route show default | awk '{print $3}'):9222 &
```

## Config
- Profile: user
- CDP URL: http://localhost:9222
- Config location: ~/.openclaw/openclaw.json → browser.profiles.user

## Capabilities
- Google Search (no captcha blocks)
- Google Console, Ads, Analytics
- Any website with Yoni's logins
- Form filling, clicking, scraping
- Screenshots

## Limitations
- Only works while Chrome is open with debug port
- If Chrome closes, need to restart with the command above
- socat bridge also needs to be running
- User-data-dir is separate profile (ChromeDebug), not main Chrome profile

## When to Use
- Web search (primary method)
- Accessing authenticated services
- Scraping sites that block headless browsers
- Any task that needs real browser with logins

## Notes
- Prefer this over headless openclaw browser for search and authenticated sites
- For simple API-accessible tasks, still use direct API calls (faster)
