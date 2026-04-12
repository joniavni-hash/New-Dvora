# Villa Lithos Media Setup - Google Drive Integration

## 🎯 הבעיה שנפתרת
- **רק תמונות מאושרות** של Villa Lithos יעלו לרשתות חברתיות
- **שליטה מלאה** על איזה תמונות מופיעות איפה
- **ניהול מרכזי** דרך Google Drive שאתה כבר מכיר

---

## 🔧 הגדרה - צעדים פשוטים

### צעד 1: Google Drive API
```bash
# אתה צריך API key מGoogle Cloud Console
# זה חינמי ולוקח 5 דקות
export GOOGLE_DRIVE_API_KEY="your_api_key_here"
```

### צעד 2: תיקיית תמונות Villa
```bash
# צור תיקיה ב-Drive עם התמונות של הוילה
# שתף: "Anyone with link can view"
# העתק את ה-folder ID מהURL
export VILLA_DRIVE_FOLDER_ID="your_folder_id_here"
```

### צעד 3: בדיקה
```bash
python3 integrations/social/villa_media_manager.py setup
```

---

## 🚀 איך זה עובד

### 1. ראה תמונות זמינות:
```bash
python3 integrations/social/villa_media_manager.py list
```
**תוצאה:**
```
📂 Villa Lithos Images in Google Drive:
   📁 villa-pool-sunset.jpg (ID: 1a2b3c...)
   ☁️ villa-aerial-view.jpg (ID: 4d5e6f...)
   📁 padel-court-action.jpg (ID: 7g8h9i...)
```

### 2. הכן תמונות לפוסט:
```bash
python3 integrations/social/villa_media_manager.py prepare 1a2b3c 4d5e6f
```
**מה קורה:**
- מוריד תמונות מGoogle Drive
- מעלה לPostiz CDN  
- מחזיר Postiz IDs לשימוש בפוסט

### 3. פרסום עם התמונות הנכונות:
```python
# במקום לנחש איזה תמונות להשתמש:
manager = VillaMediaManager()
images = manager.prepare_images_for_post(['1a2b3c', '4d5e6f'])
# עכשיו פרסם עם images['postiz_images']
```

---

## 💡 היתרונות

**✅ שליטה מלאה** - רק תמונות שאישרת עולות  
**✅ איכות גבוהה** - תמונות מקוריות, לא compressed  
**✅ ניהול קל** - העלה לDrive, זמין בכל מקום  
**✅ מעקב שימוש** - יודע איזה תמונות נוצלו איפה  
**✅ זיכרון חכם** - לא מוריד אותה תמונה פעמיים  

---

## 📋 הצעד הבא

**אתה צריך:**
1. **ליצור Google Drive folder** עם תמונות Villa Lithos אמיתיות
2. **לקבל Google Drive API key** (חינמי, 5 דקות)
3. **לשתף את התיקיה** publicly
4. **לקבל folder ID** מהURL

**אחרי זה:**  
```bash
python3 integrations/social/villa_media_manager.py list
```
**ותראה רשימה של התמונות האמיתיות שלך.**

**ואז בפעם הבאה שנפרסם - רק התמונות שלך יעלו! 🎯**