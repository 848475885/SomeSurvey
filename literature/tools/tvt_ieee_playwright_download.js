#!/usr/bin/env node
// Slow IEEE Xplore downloader using Playwright's browser pipe.
// The persistent profile remains the access surface; cookies are never read,
// exported, logged, or copied. PDF requests run inside the IEEE page context.

const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const SURVEY = path.join(ROOT, 'literature', 'ieee-tvt-semantic-communications-2023-present');
const NOTES = path.join(SURVEY, 'notes');
const PAPERS = path.join(SURVEY, 'papers');
const INCLUDED = path.join(NOTES, 'included.jsonl');
const LOG = path.join(NOTES, 'ieee_playwright_manifest.jsonl');
const PROFILE = path.join(os.homedir(), 'Documents', 'Learn Communication', '.chrome-ieee-profile');
const CHROME = path.join(process.env.ProgramFiles || 'C:\\Program Files', 'Google', 'Chrome', 'Application', 'chrome.exe');

function readJsonl(file) {
  return fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '').split(/\r?\n/).filter(Boolean).map(JSON.parse);
}

function writeJsonl(file, rows) {
  fs.writeFileSync(file, rows.map(row => JSON.stringify(row)).join('\n') + '\n', 'utf8');
}

function safeName(value, limit = 112) {
  const normalized = String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  return normalized.replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, limit).replace(/_+$/g, '') || 'paper';
}

function targetFor(row) {
  const author = ((row.authors || ['Unknown'])[0]).split(/\s+/).filter(Boolean).pop() || 'Unknown';
  return path.join(PAPERS, `${row.year}_${safeName(author, 24)}_${safeName(row.title)}.pdf`);
}

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function crossrefArnumber(doi) {
  try {
    const response = await fetch(`https://api.crossref.org/works/${encodeURIComponent(doi)}`, {
      headers: { 'User-Agent': 'Digital-SemCom-Survey/1.0 (arnumber resolver)' },
    });
    if (!response.ok) return '';
    const message = (await response.json()).message || {};
    const urls = (message.link || []).map(item => String(item.URL || ''));
    urls.push(String((((message.resource || {}).primary || {}).URL) || ''));
    for (const url of urls) {
      const query = url.match(/[?&]arnumber=(\d{7,9})/);
      if (query) return query[1];
      const file = url.match(/\/(\d{7,9})(?:-aam)?\.pdf(?:\?|$)/);
      if (file) return file[1];
    }
  } catch (_) {
    return '';
  }
  return '';
}

async function searchArnumber(page, row) {
  const url = `https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=${encodeURIComponent(row.title)}`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await sleep(5000);
  const href = await page.locator('a[href*="/document/"]').first().getAttribute('href').catch(() => '');
  const match = String(href || '').match(/\/document\/(\d{7,9})/);
  return match ? match[1] : '';
}

async function fetchPdf(page, arnumber) {
  const documentUrl = `https://ieeexplore.ieee.org/document/${arnumber}`;
  const pdfUrl = `https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=${arnumber}`;
  await page.goto(documentUrl, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await sleep(7000);
  for (let attempt = 1; attempt <= 4; attempt += 1) {
    const result = await page.evaluate(async (url) => {
      const bodyText = document.body ? document.body.innerText : '';
      const accessMatch = bodyText.match(/Access provided by:\s*([^\n]+)/);
      const response = await fetch(url, { credentials: 'include' });
      const type = response.headers.get('content-type') || '';
      const buffer = await response.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      let binary = '';
      const chunk = 0x8000;
      for (let offset = 0; offset < bytes.length; offset += chunk) {
        binary += String.fromCharCode.apply(null, bytes.subarray(offset, offset + chunk));
      }
      return {
        status: response.status,
        type,
        size: bytes.length,
        head: Array.from(bytes.slice(0, 5)).map(value => String.fromCharCode(value)).join(''),
        base64: response.status === 200 && type.toLowerCase().includes('pdf') ? btoa(binary) : '',
        access: accessMatch ? accessMatch[1].trim() : '',
        title: document.title.replace(/ \| IEEE.*$/, '').trim(),
      };
    }, pdfUrl);
    if (result.status === 200 && result.type.toLowerCase().includes('pdf') && result.head === '%PDF-') {
      return { ok: true, attempt, result, documentUrl, pdfUrl };
    }
    if (result.status === 202) {
      await sleep(12000);
      continue;
    }
    return { ok: false, attempt, result, documentUrl, pdfUrl };
  }
  return { ok: false, attempt: 4, result: {}, documentUrl, pdfUrl };
}

async function main() {
  const limitArg = process.argv.indexOf('--limit');
  const limit = limitArg >= 0 ? Number(process.argv[limitArg + 1] || 0) : 0;
  fs.mkdirSync(PAPERS, { recursive: true });
  const rows = readJsonl(INCLUDED);
  let pending = rows.filter(row => !row.pdf_valid);
  if (limit > 0) pending = pending.slice(0, limit);
  const context = await chromium.launchPersistentContext(PROFILE, {
    executablePath: CHROME,
    headless: true,
    acceptDownloads: false,
    viewport: { width: 1440, height: 1000 },
    args: ['--no-first-run'],
  });
  const page = context.pages()[0] || await context.newPage();
  page.setDefaultTimeout(90000);
  let completed = 0;
  try {
    for (let index = 0; index < pending.length; index += 1) {
      const row = pending[index];
      let arnumber = await crossrefArnumber(String(row.doi || ''));
      if (!arnumber) arnumber = await searchArnumber(page, row);
      let event;
      if (!arnumber) {
        event = { status: 'not_found', title: row.title, doi: row.doi || '' };
      } else {
        const probe = await fetchPdf(page, arnumber);
        const response = probe.result || {};
        if (probe.ok) {
          const buffer = Buffer.from(response.base64, 'base64');
          const target = targetFor(row);
          fs.writeFileSync(target, buffer);
          Object.assign(row, {
            pdf_status: 'downloaded_ieee_playwright_validated',
            pdf_path: path.resolve(target),
            pdf_valid: true,
            pdf_header_ok: true,
            pdf_bytes: buffer.length,
            sha256: sha256(buffer),
            ieee_document_id: arnumber,
            ieee_document_url: probe.documentUrl,
            ieee_pdf_url: probe.pdfUrl,
            institutional_access: response.access || '',
          });
          completed += 1;
          event = {
            status: 'downloaded', title: row.title, doi: row.doi || '', arnumber,
            bytes: buffer.length, path: target, attempt: probe.attempt,
            access: response.access || '',
          };
        } else {
          const diagnostic = path.join(NOTES, 'ieee_playwright_failure.png');
          await page.screenshot({ path: diagnostic, fullPage: false }).catch(() => {});
          event = {
            status: 'failed', title: row.title, doi: row.doi || '', arnumber,
            http_status: response.status || 0, content_type: response.type || '',
            bytes: response.size || 0, attempt: probe.attempt,
            page_title: response.title || '', diagnostic: path.relative(SURVEY, diagnostic).replace(/\\/g, '/'),
          };
        }
      }
      fs.appendFileSync(LOG, JSON.stringify(event) + '\n', 'utf8');
      writeJsonl(INCLUDED, rows);
      console.log(JSON.stringify({ n: index + 1, of: pending.length, ...event }));
      if (event.status === 'failed') break;
      await sleep(8000 + Math.floor(Math.random() * 4001));
    }
  } finally {
    await context.close();
  }
  console.log(JSON.stringify({ downloaded_this_run: completed, remaining: rows.filter(row => !row.pdf_valid).length }));
}

main().catch(error => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
