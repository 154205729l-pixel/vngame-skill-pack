#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const https = require('https');

const ROOT = path.resolve(__dirname, '..');
const BUCKET = process.env.COS_BUCKET || 'dqdai-data-1252057375';
const REGION = process.env.COS_REGION || 'ap-beijing';
const PREFIX = (process.env.COS_PREFIX || 'XiaoLiFeiDan/MBP').replace(/^\/+|\/+$/g, '');
const SECRET_ID = process.env.COS_SECRET_ID;
const SECRET_KEY = process.env.COS_SECRET_KEY;
const HOST = `${BUCKET}.cos.${REGION}.myqcloud.com`;
const ORIGIN = `https://${HOST}`;
const MANIFEST_PATH = path.join(ROOT, 'cos_asset_manifest.json');

const IMAGE_EXT = /\.(png|jpe?g|webp|gif|svg)(\?|$)/i;
const AUDIO_EXT = /\.(mp3|wav|m4a|ogg)(\?|$)/i;
const REF_KEYS = ['bg', 'photo', 'cover', 'image', 'avatar', 'src', 'bgm', 'sfx', 'amb'];

function readJson(file) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, file), 'utf8'));
}

function addRef(refs, src, where) {
  if (!src || typeof src !== 'string') return;
  const clean = src.split('?')[0];
  if (clean.startsWith('data:') || clean.startsWith('http:') || clean.startsWith('https:') || path.isAbsolute(clean)) return;
  if (!IMAGE_EXT.test(clean) && !AUDIO_EXT.test(clean)) return;
  if (!fs.existsSync(path.join(ROOT, clean))) return;
  if (!refs.has(clean)) refs.set(clean, new Set());
  refs.get(clean).add(where);
}

function walk(refs, value, where) {
  if (!value || typeof value !== 'object') return;
  if (Array.isArray(value)) {
    value.forEach((item, index) => walk(refs, item, `${where}[${index}]`));
    return;
  }
  for (const key of REF_KEYS) addRef(refs, value[key], `${where}.${key}`);
  for (const [key, child] of Object.entries(value)) {
    if (child && typeof child === 'object') walk(refs, child, `${where}.${key}`);
  }
}

function collectAssets() {
  const refs = new Map();
  const story = readJson('story.json');
  const frames = Array.isArray(story) ? story : story.frames || [];
  frames.forEach((node, index) => walk(refs, node, `story.json node ${index} ${node.type || 'unknown'}`));
  if (story.settings?.dialogSfx?.src) addRef(refs, story.settings.dialogSfx.src, 'story.json settings.dialogSfx.src');

  for (const file of ['demo.html', 'storyboard.html', '作品.html']) {
    const full = path.join(ROOT, file);
    if (!fs.existsSync(full)) continue;
    const text = fs.readFileSync(full, 'utf8');
    const re = /["']([^"']+\.(?:png|jpg|jpeg|webp|gif|svg|mp3|wav|m4a|ogg))["']/ig;
    let match;
    while ((match = re.exec(text))) addRef(refs, match[1], file);
  }

  return [...refs.entries()].map(([localPath, where]) => {
    const type = IMAGE_EXT.test(localPath) ? 'image' : 'audio';
    const fileName = path.basename(localPath);
    const key = `${PREFIX}/${type}/${fileName}`;
    const absolute = path.join(ROOT, localPath);
    return {
      localPath,
      absolute,
      type,
      key,
      url: `${ORIGIN}/${encodeURI(key)}`,
      bytes: fs.statSync(absolute).size,
      refs: [...where].sort(),
      status: 'pending',
    };
  }).sort((a, b) => a.localPath.localeCompare(b.localPath));
}

function hmac(key, data, encoding) {
  return crypto.createHmac('sha1', key).update(data).digest(encoding);
}

function sha1(data) {
  return crypto.createHash('sha1').update(data).digest('hex');
}

function encodedObjectPath(key) {
  return `/${key.split('/').map(encodeURIComponent).join('/')}`;
}

function authHeader(method, key, bodyHash, type) {
  const now = Math.floor(Date.now() / 1000);
  const expire = now + 3600;
  const keyTime = `${now};${expire}`;
  const pathname = encodedObjectPath(key);
  const httpString = `${method.toLowerCase()}\n${pathname}\n\ncontent-type=${encodeURIComponent(type)}&x-cos-content-sha1=${bodyHash}\n`;
  const stringToSign = `sha1\n${keyTime}\n${sha1(httpString)}\n`;
  const signKey = hmac(SECRET_KEY, keyTime, 'hex');
  const signature = hmac(signKey, stringToSign, 'hex');
  return `q-sign-algorithm=sha1&q-ak=${SECRET_ID}&q-sign-time=${keyTime}&q-key-time=${keyTime}&q-header-list=content-type;x-cos-content-sha1&q-url-param-list=&q-signature=${signature}`;
}

function contentType(file) {
  const ext = path.extname(file).toLowerCase();
  return {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.m4a': 'audio/mp4',
    '.ogg': 'audio/ogg',
  }[ext] || 'application/octet-stream';
}

function putObject(asset) {
  const body = fs.readFileSync(asset.absolute);
  const bodyHash = sha1(body);
  const type = contentType(asset.localPath);
  const headers = {
    Authorization: authHeader('PUT', asset.key, bodyHash, type),
    'x-cos-content-sha1': bodyHash,
    'Content-Type': type,
    'Content-Length': body.length,
    'Cache-Control': 'public, max-age=31536000, immutable',
  };
  return new Promise((resolve, reject) => {
    let settled = false;
    function done(err) {
      if (settled) return;
      settled = true;
      if (err) reject(err);
      else resolve();
    }
    const req = https.request({
      method: 'PUT',
      hostname: HOST,
      path: encodedObjectPath(asset.key),
      headers,
    }, res => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8');
        if (res.statusCode >= 200 && res.statusCode < 300) done();
        else done(new Error(`HTTP ${res.statusCode}: ${text.slice(0, 1200)}`));
      });
    });
    req.on('error', err => done(err));
    req.on('socket', socket => {
      socket.on('error', err => done(err));
    });
    req.end(body);
  });
}

async function main() {
  if (!SECRET_ID || !SECRET_KEY) {
    throw new Error('Missing COS_SECRET_ID or COS_SECRET_KEY env vars.');
  }
  let assets = collectAssets();
  const limit = Number(process.env.COS_LIMIT || 0);
  if (Number.isFinite(limit) && limit > 0) assets = assets.slice(0, limit);
  for (const asset of assets) {
    try {
      await putObject(asset);
      asset.status = 'uploaded';
    } catch (err) {
      asset.status = 'failed';
      asset.error = err.message || String(err);
    }
    fs.writeFileSync(MANIFEST_PATH, JSON.stringify({
      bucket: BUCKET,
      region: REGION,
      prefix: PREFIX,
      origin: ORIGIN,
      generatedAt: new Date().toISOString(),
      assets,
    }, null, 2), 'utf8');
  }
  const failed = assets.filter(asset => asset.status === 'failed');
  console.log(JSON.stringify({
    total: assets.length,
    uploaded: assets.length - failed.length,
    failed: failed.length,
    manifest: MANIFEST_PATH,
    image: assets.filter(asset => asset.type === 'image').length,
    audio: assets.filter(asset => asset.type === 'audio').length,
  }, null, 2));
  if (failed.length) process.exit(1);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
