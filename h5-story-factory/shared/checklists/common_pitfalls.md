# H5 剧本游戏通用坑点库

本文件记录所有 H5 剧本游戏生产中可复用的坑点。项目特定问题写到各游戏目录的 `项目复盘与防错清单.md`。

### 2026-06-06 - 不要用 file:// 验收

- 现象：本地直接打开 `file://.../demo.html` 或 `file://.../作品.html`，画面、音频、storyboard 行为和 localhost 不一致。
- 根因：`file://` 无法稳定访问 `/api/story`、音频解锁和相对资源路径，容易吃旧内置脚本。
- 处理：只用 `http://localhost:8080/storyboard.html`、`demo.html`、`作品.html` 验收。
- 以后避免：README、QA、Skill 都明确“验收只认 localhost 或线上 URL”。

### 2026-06-06 - demo 必须按 storyboard 视觉帧播放

- 现象：storyboard 正确，但 demo 掉帧，尤其 `scene` 和 `dialog` 被拆开。
- 根因：storyboard 用“一屏一帧”，demo 仍按 raw DSL node 播放。
- 处理：正式播放器也走视觉帧逻辑，`scene + 紧随 dialog/narrate` 同屏显示。
- 以后避免：任何导出作品都从 `story.json` 构建视觉帧，不手动维护 demo 内置 SCRIPT。

### 2026-06-06 - iframe / 浏览器缓存会让 storyboard 看起来没更新

- 现象：`demo.html` 已改，但 storyboard preview 仍显示旧牌面或旧素材。
- 根因：storyboard iframe 指向 `demo.html?preview=1`，可能被浏览器缓存或停在旧 file 页面。
- 处理：强刷 storyboard，必要时给 iframe 加版本参数。
- 以后避免：调试时先用 HTTP 检查 `demo.html?preview=1` 返回内容是否包含新 CSS/JS。

### 2026-06-15 - 本地部署后不要只改 demo/作品

- 现象：本地已部署并通过 storyboard 核查时，改了 `demo.html` 或 `作品.html`，用户在 storyboard 里仍看不到变化。
- 根因：storyboard iframe 会优先吃 `/api/story` 返回的 `story.json`，它可能覆盖 demo 内置 SCRIPT；只改导出版也不会改变正在看的故事板预览。
- 处理：同步修改 `story.json` 中真实运行节点，必要时重新导出 `作品.html`，并强刷 `http://localhost:8080/storyboard.html`。
- 以后避免：任何视觉/交互改动都必须先在 storyboard preview 对应帧可见，再说“已改好”；不要让用户只能去 demo 或本地导出版猜变化。

### 2026-06-16 - 保存 story.json 时 demo 内置 SCRIPT 也要同步

- 现象：storyboard 保存后 `/api/story` 是新的，但 `demo.html` fallback 内置剧本仍旧，直接打开 demo 或导出前预览会和 storyboard 不一致。
- 根因：保存接口只写 `story.json`，导出接口才替换 HTML 内置 `SCRIPT`，导致 source of truth 在日常调试中分叉。
- 处理：`POST /api/story` 成功后同步替换 `demo.html` 的 `const SCRIPT`；导出 `作品.html` 仍走导出接口。
- 以后避免：每次改保存链路或重要剧情数据后，用接口保存一次并检查响应包含同步标记，再抽查 `demo.html` 是否包含最新文案/音频 cue。

### 2026-06-16 - iframe 预览音频要有交互唤醒链路

- 现象：BGM/SFX 已配置，音频文件也存在，但 storyboard preview 或本地 demo 不主动出声。
- 根因：浏览器自动播放策略会拦截无用户手势的有声播放；父页面点击不一定自动解锁 iframe 内音频。
- 处理：preview iframe 加 `allow="autoplay"`，父页面交互时通知 iframe 重试，播放器监听 pointer/click/touch/key 后重试已有 BGM 轨道。
- 以后避免：不要只看 `story.json` 里有 BGM cue；验收时还要确认音频 URL 200、第一次交互后能播放。

### 2026-06-06 - TinyPNG API key 只在运行时注入

- 现象：图片需要批量压缩，但不能把 key 写进项目。
- 根因：API key 属于敏感信息。
- 处理：压缩前让用户通过环境变量提供 TinyPNG key，只注入当次 shell 的 `TINIFY_API_KEY`；脚本读取该变量后调用 `https://api.tinify.com/shrink`。
- 以后避免：报告和 README 只写变量名和 key 文件位置，不写真实 key；不要把 key 复制进项目文件、脚本或日志。

### 2026-06-06 - 删除未引用素材前必须备份

- 现象：`dist/assets/` 和 `Audio/` 会积累大量旧版本素材。
- 根因：反复生成和导入素材会保留多个 `_vN` 文件。
- 处理：扫描真实引用，备份未引用文件，再删除，并生成删除记录。
- 以后避免：清理脚本必须输出“保留引用”和“删除列表”，且不删除备份目录。

### 2026-06-06 - 服务器白名单要覆盖 API 和素材路径

- 现象：手机或局域网访问预览时打不开或素材缺失。
- 根因：只放通页面不够，`/api/story`、`dist/assets/*`、`Audio/*` 也要能访问。
- 处理：让运维放通 8080 端口 HTTP，以及 storyboard 所需 API 和静态路径。
- 以后避免：部署/预览前使用 `shared/deploy/server_whitelist.md` 给运维。

### 2026-06-07 - H5 静态部署不要落到 Next.js 路由里

- 现象：服务器 80/443 都通，但访问 `/h5`、`/games`、`/vn` 只得到 Next.js 404。
- 根因：Nginx 已把未知路径交给 Next.js，直接放静态文件会被应用路由吞掉。
- 处理：为每个 H5 游戏配置独立 Nginx `location ^~ /h5/{gameId}/`，并放在 Next.js 反代规则之前。
- 以后避免：部署前先 `curl -I -L` 探测目标路径；若返回 `X-Powered-By: Next.js`，说明还没有静态路径规则。

### 2026-06-16 - H5 投放链接必须带作品后缀

- 现象：单 HTML 部署到 `https://h5.aisportscfg.com/` 根路径后，后续多个作品无法从 URL 区分，广告投放和回读容易混淆。
- 根因：把域名根路径当成具体作品入口，缺少 `/h5/{gameId}/` 这一层稳定作品标识。
- 处理：默认发布到 `https://h5.aisportscfg.com/h5/{gameId}/`，例如 `https://h5.aisportscfg.com/h5/fodejiao/`；根路径只做跳转或索引，不作为投放链接。
- 以后避免：所有新增 H5 部署和广告后台跳转都使用带作品后缀的 URL；不存在的作品路径应返回 404，不要 fallback 到旧作品。

### 2026-06-07 - COS 版 HTML 要验异步素材加载

- 现象：服务器上的 `index.html` 返回 200，但首屏可能黑屏、对白音效丢失，或图片过一会儿才出现。
- 根因：HTML only 部署时，服务器只提供 HTML 壳；图片和音频都从 COS 异步加载，HTML 成功不代表素材已经成功。
- 处理：生成 `作品.cos.html` 后检查不残留 `dist/assets/` / `Audio/` 本地路径，并抽查 COS URL、首屏背景、BGM、dialog SFX。
- 以后避免：上线验收必须打开浏览器 Network 面板，确认关键图片/音频请求走 COS 且没有 404/CORS/超时；不要只用 `curl -I index.html` 判断成功。

### 2026-06-08 - 外部 App 有 Tab 时不要内置手机框

- 现象：线上 App 页面已有顶部频道栏和底部 tab，H5 内部再固定 `390x844` 手机框后，一个视口看不完整个游戏容器。
- 根因：播放器把设计预览用的手机壳尺寸带到了正式作品，真实宿主页面可见高度小于 844px。
- 处理：正式播放器使用无手机框的自适应 9:16 画布，宽高受 `100vw` 和 `visualViewport.height` 共同约束。
- 以后避免：storyboard 可以保留手机框预览，但导出的正式作品不要固定手机壳；上线必须在真实宿主 tab 环境验收。

### 2026-06-15 - Image 2 统一走 FlashAPI

- 现象：并行生成图片时，脚本在新 shell 里拿不到 key，容易被误以为要走别的 OpenAPI 入口。
- 根因：本地 `image2.py` 依赖 `FLASHAPI_KEY` 或 `OPENAI_API_KEY`，但实际请求固定打到 FlashAPI 兼容端点。
- 处理：生成图片时明确使用 `image2.py`，默认请求 `https://ai.flashapi.top/v1/images/generations` 和 `/images/edits`，不要另外改成 OpenAI OpenAPI 调用链。
- 以后避免：所有图像生成说明都写清所需环境变量，并在并行脚本里先确认 shell 环境已加载密钥。

### 2026-06-16 - story.json 才是 storyboard 之后的母文件

- 现象：修改 `剧本.md`、`demo.html` 或 `作品.html` 后，BGM、gacha 卡图、素材路径在 storyboard 里反复丢失或不同步。
- 根因：脚本源、故事板编辑态、播放器内置 `SCRIPT` 三套数据互相覆盖；从 `剧本.md` 自动同步时没有保留 storyboard 已调好的媒体字段。
- 处理：进入 storyboard 阶段后以 `story.json` 为母文件；`demo.html` 和 `作品.html` 从 `story.json` 同步/导出；`剧本.md` 自动同步只能更新结构文案，并保留 `bg/audio/bgm/sfx/cover/gacha pool/settings`。
- 以后避免：任何保存/导出链路改动后，检查 `/api/story`、`demo.html`、`作品.html` 的帧数、音频节点和 gacha 图片是否一致。

### 2026-06-16 - 本地服务启动要验证常驻而不是瞬时成功

- 现象：刚启动 storyboard server 时 curl 返回 200，但用户刷新时 Chrome 显示 `ERR_CONNECTION_REFUSED`。
- 根因：服务进程没有常驻，临时后台命令或前台会话结束后 8080 释放。
- 处理：用可保活方式启动服务，至少验证 `lsof` 有监听进程、`localhost` 和 `127.0.0.1` 都能访问、日志里没有退出。
- 以后避免：交付本地预览地址前，把端口检查和 `/api/story` 检查作为固定 QA，不只说“服务已启动”。

### 2026-06-16 - 体育叙事先核对赛程阶段和对手

- 现象：把历史背景、预选赛和正赛首战混成一条线，导致文案里同一支队伍一会儿是意大利，一会儿又变成伊拉克。
- 根因：没有先确认赛事阶段，直接按记忆写“第一战”“再遇”“赢回来”等句式。
- 处理：先用官方赛程数据确认比赛阶段和对手，再写历史回环和首战叙事。
- 以后避免：体育类 H5 里只要出现具体对手、开赛顺序、首战、晋级、淘汰，就先查赛程或权威数据源，不靠记忆写。
