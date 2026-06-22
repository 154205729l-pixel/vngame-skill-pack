#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import storyboard_server


class StoryboardWorkflowTest(unittest.TestCase):
    def test_parse_md_dsl_extracts_nodes_and_following_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / '剧本.md'
            md.write_text(
                """# test

```javascript
{ type:'scene', bg:'bg1_1.jpg', chapter:'第一章：测试' }
// bg1_1：球场灯光下的小孩点球背影。
{ type:'dialog', speaker:'小李飞蛋', text:'我叫小李飞蛋。' }
```
""",
                encoding='utf-8',
            )

            frames = storyboard_server.parse_md_dsl(md)

        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0]['type'], 'scene')
        self.assertEqual(frames[0]['id'], 'frame_001')
        self.assertIn('球场灯光', frames[0]['_hint'])
        self.assertEqual(frames[1]['speaker'], '小李飞蛋')
        self.assertEqual(frames[1]['id'], 'frame_002')

    def test_export_work_html_embeds_frames_and_removes_api_story_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo = root / 'demo.html'
            out = root / '作品.html'
            demo.write_text(
                """<script>
const SCRIPT = [
  { type:'scene', bg:'old.png' }
];
// ── 引擎 ──
const isStoryboardPreview = new URLSearchParams(window.location.search).get('preview') === '1';
// 启动：优先从 /api/story 加载，fallback 内置 SCRIPT
fetch('/api/story')
  .then(r => r.ok ? r.json() : Promise.reject())
  .then(data => { syncStoryFrames(data.frames); })
  .catch(() => {})
  .finally(() => {
    if (!isStoryboardPreview) advance();
  });

// 接收 storyboard 跳帧指令
window.addEventListener('message', e => {});
</script>""",
                encoding='utf-8',
            )

            storyboard_server.export_work_html(
                [{'type': 'scene', 'bg': 'dist/assets/new.png'}],
                demo_path=demo,
                export_path=out,
            )
            html = out.read_text(encoding='utf-8')

        self.assertIn('"dist/assets/new.png"', html)
        self.assertNotIn("fetch('/api/story')", html)
        self.assertIn('导出作品：使用内嵌 SCRIPT', html)


if __name__ == '__main__':
    unittest.main()
