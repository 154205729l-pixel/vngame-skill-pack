#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const https = require('https');

const ROOT = path.resolve(__dirname, '..');
const STORY = path.join(ROOT, 'story.json');
const REPORT = path.join(ROOT, '图片素材清单.md');
const BACKUP_DIR = path.join(ROOT, 'backup_assets_before_tinypng');
const RESULT_DIR = path.join(ROOT, '.tinypng_results');
const MANIFEST = path.join(RESULT_DIR, 'manifest.json');
const IMAGE_EXT = /\.(png|jpe?g|webp)(\?|$)/i;
const IMAGE_KEYS = ['bg', 'photo', 'cover', 'image', 'avatar', 'src'];

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function isProjectRelative(assetPath) {
  return assetPath && !assetPath.startsWith('data:') && !assetPath.startsWith('http:') && !assetPath.startsWith('https:') && !path.isAbsolute(assetPath);
}

function addRef(refs, assetPath, where) {
  if (!assetPath || typeof assetPath !== 'string' || !IMAGE_EXT.test(assetPath)) return;
  const clean = assetPath.split('?')[0];
  if (!isProjectRelative(clean)) return;
  if (!refs.has(clean)) refs.set(clean, new Set());
  refs.get(clean).add(where);
}

function walkValue(refs, value, where) {
  if (!value || typeof value !== 'object') return;
  if (Array.isArray(value)) {
    value.forEach((item, index) => walkValue(refs, item, `${where}[${index}]`));
    return;
  }
  for (const key of IMAGE_KEYS) addRef(refs, value[key], `${where}.${key}`);
  for (const [key, child] of Object.entries(value)) {
    if (child && typeof child === 'object') walkValue(refs, child, `${where}.${key}`);
  }
}

function collectRefs() {
  const refs = new Map();
  const storyPayload = readJson(STORY);
  const frames = Array.isArray(storyPayload) ? storyPayload : storyPayload.frames || [];
  frames.forEach((node, index) => walkValue(refs, node, `story.json node ${index} ${node.type || 'unknown'}`));

  for (const file of ['demo.html', 'storyboard.html', '作品.html']) {
    const full = path.join(ROOT, file);
    if (!fs.existsSync(full)) continue;
    const text = fs.readFileSync(full, 'utf8');
    const re = /["']([^"']+\.(?:png|jpg|jpeg|webp))["']/ig;
    let match;
    while ((match = re.exec(text))) addRef(refs, match[1], file);
  }

  return [...refs.entries()].map(([assetPath, whereSet]) => {
    const absolute = path.join(ROOT, assetPath);
    const exists = fs.existsSync(absolute);
    const beforeBytes = exists ? fs.statSync(absolute).size : 0;
    return {
      path: assetPath,
      absolute,
      exists,
      beforeBytes,
      afterBytes: null,
      status: exists ? 'pending' : 'missing',
      error: '',
      refs: [...whereSet].sort(),
    };
  }).sort((a, b) => a.path.localeCompare(b.path));
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function backupAssets(items) {
  ensureDir(BACKUP_DIR);
  for (const item of items) {
    if (!item.exists) continue;
    const target = path.join(BACKUP_DIR, item.path);
    ensureDir(path.dirname(target));
    if (!fs.existsSync(target)) fs.copyFileSync(item.absolute, target);
  }
}

function formatBytes(bytes) {
  if (!bytes) return '0 KB';
  const mb = bytes / 1024 / 1024;
  if (mb >= 1) return `${mb.toFixed(2)} MB`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function writeReport(items, mode) {
  const existing = items.filter(item => item.exists);
  const compressed = items.filter(item => item.status === 'compressed');
  const failed = items.filter(item => item.status === 'failed');
  const missing = items.filter(item => item.status === 'missing');
  const beforeTotal = existing.reduce((sum, item) => sum + item.beforeBytes, 0);
  const afterTotal = existing.reduce((sum, item) => sum + (item.afterBytes || item.beforeBytes), 0);
  const saved = beforeTotal - afterTotal;
  const lines = [];
  lines.push('# H5 图片素材清单与 TinyPNG 压缩记录');
  lines.push('');
  lines.push(`生成时间：${new Date().toLocaleString('zh-CN', { hour12: false })}`);
  lines.push(`执行模式：${mode}`);
  lines.push('');
  lines.push('## 压缩方式说明');
  lines.push('');
  lines.push('- 使用 TinyPNG API，不使用网页端。');
  lines.push('- API key 不写入项目文件，执行时读取环境变量 `TINIFY_API_KEY`。');
  lines.push('- 上传请求样式：`curl --user api:$TINIFY_API_KEY --data-binary @原图 https://api.tinify.com/shrink`。');
  lines.push('- 脚本读取返回 JSON 的 `output.url`，下载压缩图后覆盖原路径。');
  lines.push(`- 原图备份目录：\`${path.relative(ROOT, BACKUP_DIR)}\`。`);
  lines.push('- 回滚方式：把备份目录中的同名文件复制回项目原路径。');
  lines.push('');
  lines.push('## 汇总');
  lines.push('');
  lines.push(`- 引用图片：${items.length} 张`);
  lines.push(`- 存在图片：${existing.length} 张`);
  lines.push(`- 缺失图片：${missing.length} 张`);
  lines.push(`- 已压缩：${compressed.length} 张`);
  lines.push(`- 压缩失败：${failed.length} 张`);
  lines.push(`- 原始总大小：${formatBytes(beforeTotal)}`);
  lines.push(`- 当前总大小：${formatBytes(afterTotal)}`);
  lines.push(`- 节省：${formatBytes(Math.max(0, saved))}${beforeTotal ? `（${((saved / beforeTotal) * 100).toFixed(1)}%）` : ''}`);
  lines.push('');
  lines.push('## 素材列表');
  lines.push('');
  lines.push('| 状态 | 路径 | 压缩前 | 压缩后 | 引用位置 |');
  lines.push('|---|---|---:|---:|---|');
  for (const item of items) {
    lines.push(`| ${item.status}${item.error ? `：${item.error.replace(/\|/g, '/')}` : ''} | \`${item.path}\` | ${formatBytes(item.beforeBytes)} | ${item.afterBytes ? formatBytes(item.afterBytes) : '-'} | ${item.refs.slice(0, 4).join('<br>')} |`);
  }
  fs.writeFileSync(REPORT, lines.join('\n'), 'utf8');
}

function request(method, url, options = {}, body = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, { method, headers: options.headers || {} }, res => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve({ statusCode: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) }));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function shrinkWithTinypng(item, apiKey) {
  const body = fs.readFileSync(item.absolute);
  const auth = Buffer.from(`api:${apiKey}`).toString('base64');
  const upload = await request('POST', 'https://api.tinify.com/shrink', {
    headers: {
      Authorization: `Basic ${auth}`,
      'Content-Type': 'application/octet-stream',
      'Content-Length': body.length,
    },
  }, body);
  if (upload.statusCode < 200 || upload.statusCode >= 300) {
    throw new Error(`upload HTTP ${upload.statusCode}: ${upload.body.toString('utf8').slice(0, 180)}`);
  }
  const payload = JSON.parse(upload.body.toString('utf8'));
  const outputUrl = payload?.output?.url;
  if (!outputUrl) throw new Error('missing output.url');
  const download = await request('GET', outputUrl);
  if (download.statusCode < 200 || download.statusCode >= 300) {
    throw new Error(`download HTTP ${download.statusCode}`);
  }
  fs.writeFileSync(item.absolute, download.body);
  item.afterBytes = fs.statSync(item.absolute).size;
  item.status = item.afterBytes < item.beforeBytes ? 'compressed' : 'kept';
}

async function compressAssets(items) {
  const apiKey = process.env.TINIFY_API_KEY;
  if (!apiKey) {
    items.forEach(item => {
      if (item.exists) item.status = 'backup-only';
    });
    return 'backup-only';
  }

  for (const item of items) {
    if (!item.exists) continue;
    try {
      await shrinkWithTinypng(item, apiKey);
    } catch (err) {
      item.status = 'failed';
      item.error = err.message || String(err);
    }
    writeReport(items, 'compressing');
  }
  return 'tinypng-api';
}

async function main() {
  ensureDir(RESULT_DIR);
  const items = collectRefs();
  backupAssets(items);
  const mode = await compressAssets(items);
  fs.writeFileSync(MANIFEST, JSON.stringify(items, null, 2), 'utf8');
  writeReport(items, mode);
  const existing = items.filter(item => item.exists);
  const before = existing.reduce((sum, item) => sum + item.beforeBytes, 0);
  const after = existing.reduce((sum, item) => sum + (item.afterBytes || item.beforeBytes), 0);
  console.log(JSON.stringify({
    mode,
    count: items.length,
    existing: existing.length,
    missing: items.filter(item => !item.exists).length,
    beforeBytes: before,
    afterBytes: after,
    report: REPORT,
    backupDir: BACKUP_DIR,
  }, null, 2));
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
