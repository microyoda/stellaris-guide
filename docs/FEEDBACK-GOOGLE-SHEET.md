# Collecting Web Feedback into Google Sheets (+ Screenshots / Files)

Because `https://microyoda.github.io/stellaris-guide/` is 100% static HTML/JS with no backend server, the cleanest free way to collect player feedback **and optional screenshots/files** without requiring visitors to log in is a **Google Apps Script Web App** connected directly to your own Google Sheet and private Google Drive folder.

## Setup (2 Minutes, 100% Free)

1. **Create a Google Sheet** (e.g., name it `Stellaris Guide Feedback`).
2. In the Sheet menu, click **Extensions → Apps Script**.
3. Delete any starter code in `Code.gs`, copy the entire contents of [google-sheets-feedback.gs](./google-sheets-feedback.gs), paste it in, and click **Save**.
4. Click **Deploy → New deployment**:
   - Click the gear icon next to *Select type* → **Web app**
   - **Execute as:** `Me`
   - **Who has access:** `Anyone`
   - Click **Deploy**, approve the Google permissions prompt for your own Sheet & Drive, and copy the **Web app URL** (`https://script.google.com/macros/s/.../exec`).
5. Open `static/web-runtime.js`, paste that URL into `FEEDBACK_ENDPOINT`, and push to `main`:
   ```js
   const FEEDBACK_ENDPOINT = 'https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec';
   ```

## Security & Privacy Controls Built In
- **Opt-in attachments only:** Stellaris `.sav` files and screenshots are **never** sent automatically; a player must explicitly pick an attachment in the feedback drawer.
- **Strict file allowlist & size cap:** Only `.png`, `.jpg`, `.jpeg`, `.webp`, `.txt`, and `.sav` up to **4 MB** are accepted (blocks `.html`, `.svg`, `.js`, `.exe`).
- **Private Drive storage:** Uploaded files are saved into a **private** `Stellaris Guide Feedback` folder in your Google Drive (not publicly shared), with the Drive URL recorded in the `Attachment` column of your Sheet.
- **Formula-injection & spam protection:** Leading `=`, `+`, `-`, `@` characters are escaped before writing to Sheets, a hidden honeypot field drops basic bots, and `LockService` serializes concurrent writes.
- **Fallback before deployment:** If `FEEDBACK_ENDPOINT` is empty, feedback is saved locally in the browser and the drawer offers a **pre-filled GitHub Issue** link so feedback still works immediately.
