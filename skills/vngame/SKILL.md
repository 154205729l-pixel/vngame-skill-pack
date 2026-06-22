---
name: vngame
description: Use when creating, co-writing, storyboarding, packaging, compressing assets, cleaning resources, exporting, or deploying interactive H5 story games. Covers the full workflow from game id and Codex-assisted script co-creation through 剧本.md, story.json, storyboard preview, Image 2 prompts, asset/audio management, TinyPNG compression, 作品.html export, and static deployment.
---

# VNGame

Use this skill for H5 interactive story game work: new game creation, script co-creation, storyboard generation, asset cleanup, export, or deployment.

## Portable Project Layout

Resolve the factory root in this order:

1. `VNGAME_FACTORY_ROOT` environment variable.
2. A nearby `h5-story-factory/` folder in the current repo.
3. Ask the user where the factory is installed.

New games should live under:

```text
{factoryRoot}/games/{gameId}/
```

Shared templates and tools:

```text
{factoryRoot}/shared/engine/
{factoryRoot}/shared/tools/
{factoryRoot}/shared/prompts/
{factoryRoot}/shared/deploy/
{factoryRoot}/shared/checklists/
```

## Source Of Truth

- `剧本.md`: creative source. Co-create here first.
- `story.json`: storyboard edit state.
- `storyboard.html`: visual editor and frame preview.
- `demo.html`: shared player/export template; do not manually sync story into it.
- `作品.html`: exported final work.
- Validate with `localhost` or deployed URL. Do not treat `file://` as final truth.

## Workflow

1. **Brief**: create `game.config.json` and `创作简报.md`. Capture audience, core conflict, chapter arc, visual style, and ending logic.
2. **Co-write Script**: iterate with the user. Write chapter structure, DSL nodes, choices, gacha, endings, chapter summaries, and Image 2 prompts into `剧本.md`.
3. **Storyboard**: generate/update `story.json` from `剧本.md`, then use storyboard for frame-level bg/dialog/bgm/sfx tuning.
4. **Assets**: copy chosen images into `dist/assets/`, audio into `Audio/`, always using relative paths.
5. **Export**: use storyboard/server export to generate `作品.html`; never rely on stale inline scripts.
6. **Optimize**: run TinyPNG compression and unused image/audio cleanup only after backup.
7. **Package For Handoff**: do not deploy directly. Package `作品.html`, `dist/assets/`, `Audio/`, `story.json`, and project notes, then tell the user to send the package to Feishu colleague @李丹雅 for deployment.
8. **Retrospective**: when a new pitfall or reusable discovery appears, update the right checklist or retrospective doc.

## Key Rules

- Script is co-created, not assumed complete. Ask creative questions when the premise, tone, audience, or chapter arc is underdefined.
- Keep story changes in `剧本.md`; keep storyboard edits in `story.json`.
- For new game creation, copy shared engine/tools from the factory, then create per-game `dist/assets/`, `Audio/`, reports, and deployment records.
- Use Image 2 prompt rules for visual consistency and reusable character/art direction.
- For compression, use `TINIFY_API_KEY` env var only; never write API keys into files.
- For COS upload, use environment variables such as `COS_SECRET_ID` and `COS_SECRET_KEY`; never write credentials into files.
- Before deleting unused assets/audio, back them up and write a deletion record.
- If preview and local file disagree, trust `http://localhost:8080/...`, not `file://`.
- Do not deploy finished works directly from this public skill pack. Stop at export/package handoff; deployment should be handled by Feishu colleague @李丹雅.
- Do not leave new production knowledge only in chat; update retrospective/checklist docs.

## Useful References

Load only what is needed:

- `shared/prompts/script_co_creation.md`: when starting or revising a story.
- `shared/prompts/image2_prompt_rules.md`: when generating image prompts.
- `shared/checklists/production_qa.md`: before export/deploy.
- `shared/checklists/common_pitfalls.md`: when debugging repeated issues.
- `shared/deploy/cos_deploy.md`: when deploying to COS.
- `shared/deploy/server_whitelist.md`: when asking ops to allow local/server preview access.

## Common Commands

From a game folder:

```bash
python3 tools/storyboard_server.py
```

Open:

```text
http://localhost:8080/storyboard.html
```

If port 8080 is already in use:

```bash
PORT=8090 python3 tools/storyboard_server.py
```

Compress referenced images:

```bash
export TINIFY_API_KEY='your key'
node tools/tinypng_compress_assets.js
```

## How Users Should Invoke

Examples:

- "用 vngame 新建一个剧本游戏，主题是世界杯前夜。"
- "用 vngame 和我一起打磨第三章。"
- "用 vngame 从 剧本.md 生成 storyboard。"
- "用 vngame 压缩图片、清理未引用素材并导出作品。"
- "用 vngame 打包项目，准备交给 @李丹雅 部署。"
