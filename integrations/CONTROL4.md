# Control4 Integration
Last updated: 2026-03-18

## Status
Connected

## חשבון
- **4sight account:** Yoni-a@telefire.co.il
- **Controller:** EA-3 (control4_ea3_000FFF99B6A9)
- **Account name:** yoniavni
- **OS version:** 3.4.3 (build 727848, Nov 2024)
- **Controller IP:** 192.168.1.240

## מכשירי Control4 נוספים ברשת
- 192.168.1.102 (00:0f:ff:61:8b:df) — nginx 1.16.1, OTA page
- 192.168.1.104 (00:0f:ff:97:6f:d4) — nginx 1.24.0
- 192.168.1.115 (00:0f:ff:9a:7f:5c) — nginx 1.24.0

## גישה
- SSH: פתוח אבל דורש credentials (לא נפרץ)
- API: דרך pyControl4 + 4sight token — **עובד**
- פורטים פתוחים: 22, 80, 443

## חדרים (14)
| ID | שם |
|----|-----|
| 14 | סלון |
| 38 | מטבח |
| 39 | בריכה |
| 40 | ברביקיו |
| 41 | פינת ישיבה בריכה |
| 46 | פטיו |
| 93 | חדר הורים |
| 94 | פינת משפחה |
| 95 | חדר אלון |
| 96 | ממד |
| 97 | מקלחת ילדים |
| 219 | מדרגות |
| 220 | שירותי אורחים |
| 294 | מקלחת הורים |

## מכשירים עיקריים
- ~50 תאורות KNX (on/off, חלקם ללא dimmer)
- 9 תריסים/וילונות KNX
- 6 אזורי מיזוג CoolMaster
- 5 טלוויזיות LG (OLED)
- Sonos Move + Triad One x2 (מולטירום)
- Yamaha RX-V6A (receiver)
- Paradox אזעקה
- Control4 DS2 אינטרקום + מנעול דלת
- 5 מצלמות Hikvision
- אח, מזרקה, דוד חשמל

## שימוש טכני
```python
from pyControl4.account import C4Account
from pyControl4.director import C4Director

account = C4Account("Yoni-a@telefire.co.il", "control4u")
await account.get_account_bearer_token()
controllers = await account.get_account_controllers()
director_token = await account.get_director_bearer_token(controllers['controllerCommonName'])
director = C4Director("192.168.1.240", director_token['token'])

# Read state
vars = await director.get_item_variables(ITEM_ID)
# Send command
await director.send_item_command(ITEM_ID, "ON")
await director.send_item_command(ITEM_ID, "OFF")
```

## סטטוס
- ✅ קריאת מצב תאורות
- ✅ שליחת פקודות (ON/OFF/TOGGLE)
- ⏳ לא נבדק עדיין: תריסים, מיזוג, תרחישים
- ⏳ ממתין לבדיקה פיזית עם יוני בבית
