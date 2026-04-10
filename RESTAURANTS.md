# RESTAURANTS.md

מטרת הקובץ: להפוך חיפוש והזמנת מסעדות לתהליך מהיר, יעיל וזול.

## כלל עבודה
במסעדות בתל אביב והסביבה:
1. קודם לבדוק אם המסעדה יושבת על **Ontopo**
2. אם לא, לבדוק **Tabit**
3. דפדפן רק אם אין דרך אחרת

## סטטוסי זמינות
- `seat` = יש שולחן לאישור מיידי
- `callback` = בקשה לצוות האירוח
- `disabled` = אין מקום

## מסעדות ידועות

### Claro
- Provider: Ontopo
- URL: https://ontopo.com/en/il/page/24489442
- Slug: `24489442`
- Venue ID: `46110568`
- Notes: אפשר לשלוף זמינות דרך `/api/availability_search`

### ים 7
- Provider: Ontopo
- URL: https://ontopo.com/he/il/page/85703946
- Slug: `85703946`
- Venue ID: `46110568`
- Notes: ב-TABIT יש חסימת CloudFront מהשרת, אז עדיף Ontopo/API

### יפו תל אביב
- Provider: Ontopo
- URL: https://ontopo.com/he/il/page/34362976
- Slug: `34362976`
- Venue ID: `53643274`
- Notes: זמינות נשלפת היטב דרך API פנימי

## API Pattern ל-Ontopo
POST `https://ontopo.com/api/availability_search`

Payload pattern:
```json
{
  "slug": "<restaurant-slug>",
  "locale": "he",
  "criteria": {
    "date": "YYYYMMDD",
    "time": "HHMM",
    "size": "<party-size>"
  },
  "data": {
    "analytics": {
      "market_id": "",
      "venue_id": "<venue-id>",
      "referrer_domain": null,
      "device_id": "<device-id>",
      "platform": "web",
      "distributor_id": "il",
      "origin": "venue_page",
      "sub_origin": null
    }
  }
}
```

## תשובה למשתמש
להחזיר רק:
- האם יש מקום או לא
- השעות הרלוונטיות
- האם זה אישור מיידי או בקשה לצוות
- בלי לפרט תהליך
