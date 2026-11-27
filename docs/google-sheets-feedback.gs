/**
 * Stellaris Guide — Free Google Sheets + Google Drive Feedback Receiver
 *
 * Deploy as a Google Apps Script Web App bound to your Google Sheet:
 *   1. Open a new Google Sheet -> Extensions -> Apps Script
 *   2. Paste this entire file into Code.gs and Save
 *   3. Click Deploy -> New deployment -> Web app
 *      - Execute as: Me
 *      - Who has access: Anyone
 *   4. Copy the Web App URL (https://script.google.com/macros/s/.../exec)
 *      and paste it into FEEDBACK_ENDPOINT in static/web-runtime.js
 */

const SHEET_NAME = 'Feedback';
const DRIVE_FOLDER_NAME = 'Stellaris Guide Feedback';
const MAX_COMMENT_LEN = 1000;
const MAX_FILE_BYTES = 4 * 1024 * 1024; // 4 MB decoded
const MAX_BASE64_LEN = 5800000;
const MAX_SUBMISSIONS_PER_HOUR = 60;
const MAX_UPLOADS_PER_DAY = 25;

const ALLOWED_EXTENSIONS = {
  png: 'image/png',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  webp: 'image/webp',
  txt: 'text/plain',
  sav: 'application/zip',
};

function validationError(message) {
  const err = new Error(message);
  err.isValidation = true;
  return err;
}

function safeCell(value, maxLen) {
  let str = String(value == null ? '' : value).replace(/\u0000/g, '').trim();
  if (str.length > maxLen) str = str.slice(0, maxLen);
  // Prevent Google Sheets formula injection.
  if (/^[=+\-@\t\r]/.test(str)) str = "'" + str;
  return str;
}

function checkRateLimit(hasAttachment) {
  const cache = CacheService.getScriptCache();
  const hourKey = 'fb_hr_' + Utilities.formatDate(new Date(), 'UTC', 'yyyyMMddHH');
  const hourCount = Number(cache.get(hourKey) || 0);
  if (hourCount >= MAX_SUBMISSIONS_PER_HOUR) {
    throw validationError('Feedback rate limit reached. Please try again later.');
  }
  cache.put(hourKey, String(hourCount + 1), 3600);

  if (hasAttachment) {
    const dayKey = 'fb_up_' + Utilities.formatDate(new Date(), 'UTC', 'yyyyMMdd');
    const dayCount = Number(cache.get(dayKey) || 0);
    if (dayCount >= MAX_UPLOADS_PER_DAY) {
      throw validationError('Daily attachment limit reached. Please submit without an attachment or try tomorrow.');
    }
    cache.put(dayKey, String(dayCount + 1), 21600);
  }
}

function bytesMatch(bytes, offset, expected) {
  if (bytes.length < offset + expected.length) return false;
  for (let i = 0; i < expected.length; i++) {
    if ((bytes[offset + i] & 0xff) !== expected[i]) return false;
  }
  return true;
}

function verifyMagicBytes(ext, bytes) {
  if (!bytes || bytes.length === 0) throw validationError('Attached file is empty.');
  if (ext === 'png') {
    if (!bytesMatch(bytes, 0, [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) {
      throw validationError('File content does not match a valid PNG image.');
    }
  } else if (ext === 'jpg' || ext === 'jpeg') {
    if (!bytesMatch(bytes, 0, [0xff, 0xd8, 0xff])) {
      throw validationError('File content does not match a valid JPEG image.');
    }
  } else if (ext === 'webp') {
    if (!bytesMatch(bytes, 0, [0x52, 0x49, 0x46, 0x46]) || !bytesMatch(bytes, 8, [0x57, 0x45, 0x42, 0x50])) {
      throw validationError('File content does not match a valid WebP image.');
    }
  } else if (ext === 'sav') {
    if (!bytesMatch(bytes, 0, [0x50, 0x4b, 0x03, 0x04])) {
      throw validationError('File content does not match a valid Stellaris .sav archive.');
    }
  } else if (ext === 'txt') {
    const sample = Math.min(bytes.length, 4096);
    for (let i = 0; i < sample; i++) {
      if ((bytes[i] & 0xff) === 0x00) throw validationError('Invalid binary content in text file.');
    }
  }
}

function getOrCreateSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow([
      'Timestamp (UTC)', 'Rating', 'Reason', 'Comment',
      'View', 'App Version', 'Game Version', 'Attachment',
    ]);
  }
  return sheet;
}

function getOrCreateFolder() {
  const iter = DriveApp.getFoldersByName(DRIVE_FOLDER_NAME);
  if (iter.hasNext()) return iter.next();
  // Kept private to your Google Drive account by default.
  return DriveApp.createFolder(DRIVE_FOLDER_NAME);
}

function saveAttachment(attachment) {
  if (!attachment || typeof attachment !== 'object') return '';
  const rawName = String(attachment.name || '').trim();
  const match = rawName.toLowerCase().match(/\.([a-z0-9]+)$/);
  const ext = match ? match[1] : '';
  if (!Object.prototype.hasOwnProperty.call(ALLOWED_EXTENSIONS, ext)) {
    throw validationError('Unsupported attachment type. Allowed: PNG, JPG, WebP, TXT, SAV.');
  }
  const b64 = String(attachment.data_base64 || '');
  if (!b64 || b64.length > MAX_BASE64_LEN || !/^[A-Za-z0-9+/=]+$/.test(b64)) {
    throw validationError('Attachment payload is invalid or exceeds the 4 MB limit.');
  }
  const bytes = Utilities.base64Decode(b64);
  if (bytes.length === 0 || bytes.length > MAX_FILE_BYTES) {
    throw validationError('Attachment must be non-empty and at most 4 MB.');
  }
  verifyMagicBytes(ext, bytes);
  const stamp = Utilities.formatDate(new Date(), 'UTC', 'yyyyMMdd-HHmmss');
  const rawStem = rawName.slice(0, -(ext.length + 1));
  const cleanStem = rawStem.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 64) || 'upload';
  const blob = Utilities.newBlob(bytes, ALLOWED_EXTENSIONS[ext], stamp + '_' + cleanStem + '.' + ext);
  const folder = getOrCreateFolder();
  const file = folder.createFile(blob);
  return file.getUrl();
}

function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    if (!lock.tryLock(10000)) {
      return jsonResponse({ok: false, error: 'Server busy; please try again.'});
    }
    const raw = (e && e.postData && e.postData.contents) ? e.postData.contents : '';
    if (!raw || raw.length > MAX_BASE64_LEN + 8192) {
      throw validationError('Request payload is empty or too large.');
    }
    let data;
    try {
      data = JSON.parse(raw);
    } catch (_) {
      throw validationError('Malformed JSON payload.');
    }

    // Honeypot spam filter: real users never fill the hidden "website" field.
    if (data.website && String(data.website).trim() !== '') {
      return jsonResponse({ok: true});
    }

    const rating = String(data.rating || '').trim();
    if (rating !== 'useful' && rating !== 'not_useful') {
      throw validationError('Invalid rating.');
    }

    checkRateLimit(Boolean(data.attachment));

    let attachmentUrl = '';
    if (data.attachment) {
      attachmentUrl = saveAttachment(data.attachment);
    }

    const sheet = getOrCreateSheet();
    sheet.appendRow([
      new Date().toISOString(),
      safeCell(rating, 20),
      safeCell(data.reason || '', 80),
      safeCell(data.comment || '', MAX_COMMENT_LEN),
      safeCell(data.view || 'main', 40),
      safeCell(data.app_version || '', 40),
      safeCell(data.game_version || '', 80),
      attachmentUrl,
    ]);
    return jsonResponse({ok: true});
  } catch (err) {
    const msg = (err && err.isValidation) ? err.message : 'Could not record feedback right now. Please try again.';
    return jsonResponse({ok: false, error: msg});
  } finally {
    try { lock.releaseLock(); } catch (_) {}
  }
}
