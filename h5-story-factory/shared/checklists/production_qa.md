# 生产验收清单

## 剧本

- `剧本.md` 和 `story.json` 不互相覆盖。
- 章节标题、章节总结、转场、结局完整。
- 没有真实 logo、队徽、品牌、赞助商或可识别真实肖像。
- 剧本先能让玩家理解角色和情感旅程，再检查悬疑、设定和答案是否成立。
- 每个核心角色至少能说清欲望、恐惧、秘密、关系位置，不把配角写成单纯工具人。
- 每个互动节点都应推进角色理解、关系变化或情绪选择，不能只是考玩家猜谜底。
- 结局要有情绪余味；不为了显得聪明而牺牲“有情有感”。
- 涉及真实赛事时，先核对比赛阶段、日期和对手，再写历史回环或首战文案，避免把预选赛、正赛和历史背景混写。

## Storyboard

- 左侧视觉帧是一屏一帧。
- `scene + dialog/narrate` 同屏显示。
- 点击 preview 时左侧进度同步。
- BGM/SFX 轨道显示正确，没有旧 BGM 残留。
- 本地服务已启动时，每次视觉/交互改动都必须先在 `storyboard.html` 的 preview 对应帧可见；不要只改 `demo.html` 或 `作品.html`。
- 如果 preview 依赖 `/api/story`，同步检查 `story.json` 里的运行字段是否也已更新，例如抽卡 `pool.image`、素材路径、文案和分值。

## 素材

- 所有 `dist/assets/` 引用存在。
- 所有 `Audio/` 引用存在。
- 图片压缩后有备份和报告。
- 压缩前通过环境变量读取 TinyPNG key，只注入当次命令的 `TINIFY_API_KEY`。
- 未引用图片/音频删除前有备份和删除记录。

## 导出

- `作品.html` 由 storyboard 导出。
- 不使用 `file://` 验收。
- `demo.html`、`storyboard.html`、`作品.html` 脚本语法检查通过。
- demo/作品必须和 storyboard 一样按视觉帧播放，不能按 raw DSL node 掉帧。
- 保存 storyboard 后，确认 `POST /api/story` 同步更新 `story.json` 和 `demo.html` 内置 `SCRIPT`；导出后再确认 `作品.html` 同步。
- storyboard iframe 如疑似缓存，强刷或加版本参数后再判断。
- 导出前先确认 storyboard preview 已经展示最新改动；导出后再打开 `作品.html` 复核，不能反过来只看导出版。
- 生成 COS 版 HTML 后，检查 HTML 中不残留 `dist/assets/` 或 `Audio/` 本地路径。
- COS 版 HTML 是异步加载远端图片/音频，不能只看 HTML 200；必须等首屏背景、对白音效、BGM 至少各加载一次。
- 章节背景 SVG、gacha 卡池文案、`tools/normalize_story.py` 这类派生内容也算验收对象，不能只搜正文。

## 上线

- 线上 URL 能打开。
- 首屏、选择题、抽卡、结局页正常。
- 手机屏幕 dialog 不溢出容器。
- 嵌入带顶部/底部 tab 的宿主页面时，一个视口内能看到完整 H5 容器，不需要页面滚动。
- 图片和音频路径都能通过 HTTP 访问，不依赖本机绝对路径。
- BGM/SFX 验收要包含首次交互后的播放测试；cue 存在和文件 200 不代表浏览器已允许出声。
- 浏览器 Network 面板里图片/音频请求应走 COS 域名，且关键素材没有 404/CORS/超时。
- 慢网或首次打开时首屏不能长期黑屏；如背景还在异步加载，应有已知占位或可恢复刷新。
