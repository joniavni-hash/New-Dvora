# Google Drive Connection - WORKING ✅

## Status: CONNECTED AND FUNCTIONAL
**Date:** 2026-03-24 19:13
**Account:** joni.avni@gmail.com
**Auth Method:** OAuth via gog CLI

## Working Commands
```bash
# List Villa Lithos photos
export GOG_KEYRING_PASSWORD="" && gog drive ls --parent "1x2qEmoYopOtlhXWQfunQ5H7a_hy2oisI" --account joni.avni@gmail.com

# Download specific file
export GOG_KEYRING_PASSWORD="" && gog drive download [FILE_ID] --account joni.avni@gmail.com
```

## Key Learning: KEYRING PASSWORD
**Critical:** Always use `export GOG_KEYRING_PASSWORD=""` before gog commands
Without this, commands fail with "no TTY available for keyring file backend password prompt"

## Villa Lithos Folder
- **Folder ID:** `1x2qEmoYopOtlhXWQfunQ5H7a_hy2oisI`
- **Public URL:** https://drive.google.com/drive/folders/1x2qEmoYopOtlhXWQfunQ5H7a_hy2oisI
- **Total Images:** 19 files (89KB - 11.8MB each)
- **Storage:** All high-quality Villa photos available

## Auth Details
- **Client ID:** YOUR_GOOGLE_CLIENT_ID_HERE
- **Scopes:** email, drive, userinfo.email, openid
- **OAuth Flow:** Successfully completed via browser
- **Token Storage:** gog keyring (requires empty password)

## Test Results ✅
```
19 images successfully listed including:
- Copy of IMG_0160.jpg (8.8 MB) - exterior view
- Copy of IMG_0139.jpg (8.3 MB) - dining area  
- Copy of IMG_0151.jpg (9.7 MB) - living space
- Copy of IMG_0132-2.jpg (11.8 MB) - sunset view
- IMG_8363.jpeg (4.1 MB) - recent photo
```

## Integration Status
- **Google Drive API:** ✅ WORKING
- **File Access:** ✅ WORKING  
- **Villa Lithos Images:** ✅ ACCESSIBLE
- **Ready for:** Automated social media posting

## DO NOT LOSE THIS CONNECTION
This took multiple attempts to establish. The auth tokens are stored in gog keyring.
If connection is lost, re-run: `gog auth add joni.avni@gmail.com --services drive`

## Recovery Instructions
If connection fails:
1. `export GOG_KEYRING_PASSWORD=""`
2. `gog auth add joni.avni@gmail.com --services drive`  
3. Follow OAuth flow in browser
4. Test with Villa folder listing command above