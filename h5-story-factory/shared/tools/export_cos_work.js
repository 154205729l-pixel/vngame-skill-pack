#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SOURCE = path.join(ROOT, '作品.html');
const TARGET = path.join(ROOT, '作品.cos.html');
const MANIFEST = path.join(ROOT, 'cos_asset_manifest.json');

function replaceAllLiteral(input, from, to) {
  return input.split(from).join(to);
}

function main() {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  let html = fs.readFileSync(SOURCE, 'utf8');
  const uploaded = manifest.assets.filter(asset => asset.status === 'uploaded');
  for (const asset of uploaded) {
    html = replaceAllLiteral(html, asset.localPath, asset.url);
  }
  fs.writeFileSync(TARGET, html, 'utf8');
  console.log(JSON.stringify({
    output: TARGET,
    replaced: uploaded.length,
    origin: manifest.origin,
  }, null, 2));
}

main();
