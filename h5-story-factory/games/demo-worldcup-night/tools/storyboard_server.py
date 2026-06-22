#!/usr/bin/env python3
"""
本地剧本编辑服务 — http://localhost:8080
接口：
  GET  /api/story          读取 story.json
  POST /api/story          保存 story.json
  POST /api/assets         上传图片到 dist/assets/
  POST /api/audio          上传音频到 Audio/
  GET  /api/audio-list     列出 Audio/ 中的已有音频
  POST /api/export-work    导出正式作品 HTML
  GET  /                   静态文件服务（项目根目录）
"""
import hashlib, http.server, json, os, shutil, urllib.parse, mimetypes, re, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
STORY = ROOT / 'story.json'
MD = ROOT / '剧本.md'
DEMO = ROOT / 'demo.html'
EXPORT = ROOT / '作品.html'
ASSETS = ROOT / 'dist' / 'assets'
AUDIO = ROOT / 'Audio'
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}

NODE_MD_PARSER = r"""
const fs = require('fs');
const vm = require('vm');

const mdPath = process.argv[1];
const md = fs.readFileSync(mdPath, 'utf8');
const fenceRe = /```(?:javascript|js)\s*\n([\s\S]*?)```/gi;
const nodes = [];

function findObjectEnd(code, start) {
  let depth = 0;
  let quote = null;
  let escape = false;
  let lineComment = false;
  let blockComment = false;

  for (let i = start; i < code.length; i++) {
    const ch = code[i];
    const next = code[i + 1];

    if (lineComment) {
      if (ch === '\n') lineComment = false;
      continue;
    }
    if (blockComment) {
      if (ch === '*' && next === '/') {
        blockComment = false;
        i++;
      }
      continue;
    }
    if (quote) {
      if (escape) {
        escape = false;
      } else if (ch === '\\') {
        escape = true;
      } else if (ch === quote) {
        quote = null;
      }
      continue;
    }

    if (ch === '/' && next === '/') {
      lineComment = true;
      i++;
      continue;
    }
    if (ch === '/' && next === '*') {
      blockComment = true;
      i++;
      continue;
    }
    if (ch === "'" || ch === '"' || ch === '`') {
      quote = ch;
      continue;
    }
    if (ch === '{') depth++;
    if (ch === '}') {
      depth--;
      if (depth === 0) return i + 1;
    }
  }
  return -1;
}

function readFollowingHint(code, end) {
  const rest = code.slice(end);
  const lines = rest.split(/\r?\n/);
  const hints = [];
  for (const line of lines) {
    if (!line.trim()) {
      if (hints.length) break;
      continue;
    }
    const match = line.match(/^\s*\/\/\s*((?:bg|p)[^\r\n]*)/i);
    if (!match) break;
    hints.push(match[1].trim());
  }
  return hints.join('\n');
}

function scanBlock(code) {
  let i = 0;
  while (i < code.length) {
    const start = code.indexOf('{', i);
    if (start < 0) break;
    const end = findObjectEnd(code, start);
    if (end < 0) break;

    const literal = code.slice(start, end);
    i = end;
    if (!/\btype\s*:/.test(literal)) continue;

    try {
      const node = vm.runInNewContext(`(${literal})`, Object.create(null), { timeout: 1000 });
      if (!node || typeof node !== 'object' || !node.type) continue;
      const hint = readFollowingHint(code, end);
      if (hint && !node._hint) node._hint = hint;
      nodes.push(node);
    } catch (err) {
      throw new Error(`无法解析剧本节点：${literal.slice(0, 120)}\n${err.message}`);
    }
  }
}

let match;
while ((match = fenceRe.exec(md))) scanBlock(match[1]);

nodes.forEach((node, index) => {
  if (!node.id) node.id = `frame_${String(index + 1).padStart(3, '0')}`;
});

process.stdout.write(JSON.stringify(nodes));
"""


def parse_md_dsl(md_path=MD):
    """Extract flat DSL nodes from javascript code fences in 剧本.md."""
    md_path = Path(md_path)
    if not md_path.exists():
        return []
    result = subprocess.run(
        ['node', '-e', NODE_MD_PARSER, str(md_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout or '[]')


def maybe_sync_story_from_md(story_path=STORY, md_path=MD):
    """Refresh story.json from 剧本.md only when markdown is newer."""
    story_path = Path(story_path)
    md_path = Path(md_path)
    if not md_path.exists():
        return False
    if story_path.exists() and story_path.stat().st_mtime >= md_path.stat().st_mtime:
        return False

    frames = parse_md_dsl(md_path)
    if not frames:
        return False

    story_path.write_text(
        json.dumps({'frames': frames}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return True


def merge_transition_covers_from_md(payload, md_path=MD):
    """Keep transition cover values from 剧本.md when story edits omit them."""
    if not Path(md_path).exists():
        return payload, False
    try:
        md_nodes = parse_md_dsl(md_path)
    except Exception as exc:
        print(f'转场封面同步失败：{exc}')
        return payload, False

    by_id = {}
    by_key = {}
    for node in md_nodes:
        if node.get('type') != 'transition' or not node.get('cover'):
            continue
        if node.get('id'):
            by_id[node['id']] = node['cover']
        by_key[(node.get('text'), node.get('chapter'))] = node['cover']

    frames = payload.get('frames', payload if isinstance(payload, list) else [])
    changed = False
    for node in frames:
        if node.get('type') != 'transition' or node.get('cover'):
            continue
        cover = by_id.get(node.get('id')) or by_key.get((node.get('text'), node.get('chapter')))
        if cover:
            node['cover'] = cover
            changed = True
    return payload, changed


def export_work_html(frames, settings=None, demo_path=DEMO, export_path=EXPORT):
    if not frames:
        raise ValueError('story.json 没有可导出的帧，已取消导出。')
    demo_path = Path(demo_path)
    export_path = Path(export_path)
    html = demo_path.read_text(encoding='utf-8')
    script_json = json.dumps(frames or [], ensure_ascii=False, indent=2)

    html, script_count = re.subn(
        r"const SCRIPT = \[[\s\S]*?\];\s*\n(?=// ── 引擎)",
        lambda _match: f"const SCRIPT = {script_json};\n",
        html,
        count=1,
    )
    if script_count != 1:
        raise ValueError('没有在 demo.html 中找到可替换的 SCRIPT 模板。')

    html, boot_count = re.subn(
        r"// 启动：优先从 /api/story 加载，fallback 内置 SCRIPT[\s\S]*?(?=\n// 接收 storyboard 跳帧指令)",
        lambda _match: (
            "// 导出作品：使用内嵌 SCRIPT，不依赖 /api/story\n"
            f"_initDialogSfx({json.dumps((settings or {}).get('dialogSfx', {'src':'Audio/对话框出现.mp3','volume':0.7,'enabled':True}), ensure_ascii=False)});\n"
            "if (!isStoryboardPreview) startVisualPlayback();\n"
        ),
        html,
        count=1,
    )
    if boot_count != 1:
        raise ValueError('没有在 demo.html 中找到启动加载模板。')

    export_path.write_text(html, encoding='utf-8')
    return export_path


def read_story_frames():
    if not STORY.exists():
        return []
    data = json.loads(STORY.read_text(encoding='utf-8') or '{"frames":[]}')
    return data.get('frames', data if isinstance(data, list) else [])

def read_story_payload():
    if not STORY.exists():
        return {'frames': [], 'settings': {}}
    data = json.loads(STORY.read_text(encoding='utf-8') or '{"frames":[]}')
    if isinstance(data, list):
        return {'frames': data, 'settings': {}}
    return {
        'frames': data.get('frames', []) if isinstance(data.get('frames'), list) else [],
        'settings': data.get('settings', {}) if isinstance(data.get('settings'), dict) else {},
    }

def get_payload_frames(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        frames = payload.get('frames')
        return frames if isinstance(frames, list) else []
    return []

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f'[{self.address_string()}]', fmt % args)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _send_bytes(self, data, content_type, status=200, cache='no-cache'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', cache)
        self.send_header('Connection', 'close')
        self._cors()
        self.end_headers()
        if data:
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass
        self.close_connection = True

    def _json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self._send_bytes(data, 'application/json; charset=utf-8', status=status, cache='no-cache')

    def do_OPTIONS(self):
        self._send_bytes(b'', 'text/plain; charset=utf-8', status=204, cache='no-cache')

    def do_GET(self):
        path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)

        if path == '/api/story':
            try:
                maybe_sync_story_from_md()
            except Exception as exc:
                print(f'剧本.md 自动同步失败：{exc}')
            if STORY.exists():
                payload = json.loads(STORY.read_text(encoding='utf-8') or '{"frames":[]}')
                payload, changed = merge_transition_covers_from_md(payload)
                if changed:
                    STORY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            else:
                data = b'{"frames":[]}'
            self._send_bytes(data, 'application/json; charset=utf-8', cache='no-cache')
            return

        if path == '/api/audio-list':
            self._json({'files': self._list_audio_files()})
            return

        # 静态文件
        file_path = ROOT / path.lstrip('/')
        if file_path.is_dir():
            file_path = file_path / 'index.html'
        if not file_path.exists():
            self._send_bytes(b'Not Found', 'text/plain; charset=utf-8', status=404, cache='no-cache')
            return
        mime, _ = mimetypes.guess_type(str(file_path))
        suffix = file_path.suffix.lower()
        cache = 'public, max-age=3600' if suffix in {
            '.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.mp3', '.wav', '.m4a', '.ogg', '.woff', '.woff2'
        } else 'no-cache'
        self._send_bytes(file_path.read_bytes(), mime or 'application/octet-stream', cache=cache)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        if path == '/api/story':
            try:
                payload = json.loads(body.decode('utf-8') or '{"frames":[]}')
                frames = get_payload_frames(payload)
                if not frames:
                    self._json({'ok': False, 'error': '拒绝保存空故事：frames 为空。'}, status=400)
                    return
                payload, _ = merge_transition_covers_from_md(payload)
                STORY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
            except Exception as exc:
                print(f'保存 story.json 时保留转场封面失败：{exc}')
                STORY.write_bytes(body)
            self._send_bytes(b'{"ok":true}', 'application/json; charset=utf-8', cache='no-cache')
            return

        if path == '/api/assets':
            self._handle_upload(body, self.headers.get('Content-Type', ''), ASSETS, 'dist/assets')
            return

        if path == '/api/audio':
            self._handle_upload(body, self.headers.get('Content-Type', ''), AUDIO, 'Audio', dedupe=True)
            return

        if path == '/api/export-work':
            try:
                payload = read_story_payload()
                export_path = export_work_html(payload['frames'], payload.get('settings'))
                self._json({
                    'ok': True,
                    'path': export_path.name,
                    'absolutePath': str(export_path),
                    'deployRoot': str(ROOT),
                    'deployFiles': [export_path.name, 'dist/assets/', 'Audio/'],
                    'url': f'/{urllib.parse.quote(export_path.name)}',
                })
            except Exception as exc:
                self._json({'ok': False, 'error': str(exc)}, status=500)
            return

        self._send_bytes(b'Not Found', 'text/plain; charset=utf-8', status=404, cache='no-cache')

    def _safe_filename(self, name, dest):
        decoded = urllib.parse.unquote(name or 'asset')
        base = Path(decoded.replace('\\', '/')).name.strip() or 'asset'
        base = re.sub(r'[\x00-\x1f<>:"/\\|?*]+', '_', base)
        stem = Path(base).stem or 'asset'
        suffix = Path(base).suffix
        candidate = f'{stem}{suffix}'
        i = 2
        while (dest / candidate).exists():
            candidate = f'{stem}_v{i}{suffix}'
            i += 1
        return candidate

    def _list_audio_files(self):
        AUDIO.mkdir(parents=True, exist_ok=True)
        files = []
        for path in AUDIO.iterdir():
            if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            stat = path.stat()
            files.append({
                'name': path.name,
                'path': f'Audio/{path.name}',
                'size': stat.st_size,
                'mtime': stat.st_mtime,
            })
        return sorted(files, key=lambda item: item['name'].lower())

    def _sha256(self, data):
        return hashlib.sha256(data).hexdigest()

    def _find_existing_upload(self, data, dest, public_prefix):
        incoming = self._sha256(data)
        if not dest.exists():
            return None
        for path in sorted(dest.iterdir(), key=lambda p: p.name.lower()):
            if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest() == incoming:
                    return {
                        'path': f'{public_prefix}/{path.name}',
                        'duplicate': True,
                        'existingPath': f'{public_prefix}/{path.name}',
                    }
            except OSError:
                continue
        return None

    def _handle_upload(self, body, content_type, dest, public_prefix, dedupe=False):
        if 'multipart' not in content_type or 'boundary=' not in content_type:
            self._send_bytes(b'Bad Request', 'text/plain; charset=utf-8', status=400, cache='no-cache')
            return
        boundary = content_type.split('boundary=')[-1].encode()
        parts = body.split(b'--' + boundary)
        for part in parts[1:-1]:
            header, _, data = part.partition(b'\r\n\r\n')
            disp = [l for l in header.split(b'\r\n') if b'filename' in l]
            if not disp: continue
            raw_name = disp[0].split(b'filename="')[1].split(b'"')[0].decode(errors='ignore')
            if data.endswith(b'\r\n'):
                data = data[:-2]
            dest.mkdir(parents=True, exist_ok=True)
            if dedupe:
                existing = self._find_existing_upload(data, dest, public_prefix)
                if existing:
                    self._json(existing)
                    return
            fname = self._safe_filename(raw_name, dest)
            (dest / fname).write_bytes(data)
            self._json({'path': f'{public_prefix}/{fname}', 'duplicate': False})
            return
        self._send_bytes(b'Bad Request', 'text/plain; charset=utf-8', status=400, cache='no-cache')

if __name__ == '__main__':
    ASSETS.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get('PORT', '8080'))
    addr = ('', port)
    httpd = http.server.ThreadingHTTPServer(addr, Handler)
    print(f'Storyboard server → http://localhost:{port}')
    print(f'  story.json : {STORY}')
    print(f'  assets/    : {ASSETS}')
    print(f'  audio/     : {AUDIO}')
    httpd.serve_forever()
