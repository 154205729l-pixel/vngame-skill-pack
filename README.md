# vngame skill pack

这是给同事安装的 vngame 轻量包，包含：

- `skills/vngame/`: Codex skill 本体
- `h5-story-factory/shared/`: 公共 H5 剧情游戏模板、工具、提示词和检查清单
- `h5-story-factory/games/demo-worldcup-night/`: 一个不含私有素材的 demo 项目

## 安装

在仓库根目录执行：

```bash
./install.sh
```

安装脚本会把 skill 复制到 `~/.codex/skills/vngame`，并提示把本仓库的工厂目录设为：

```bash
export VNGAME_FACTORY_ROOT="$(pwd)/h5-story-factory"
```

建议把这行加到自己的 shell 配置文件里。

## 试跑 demo

```bash
cd h5-story-factory/games/demo-worldcup-night
python3 tools/storyboard_server.py
```

然后打开：

```text
http://localhost:8080/storyboard.html
```

如果 8080 被占用，可以换端口：

```bash
PORT=8090 python3 tools/storyboard_server.py
```

## 给 Codex 的调用示例

- `用 vngame 新建一个世界杯互动剧情游戏。`
- `用 vngame 和我一起打磨第二章剧本。`
- `用 vngame 从 剧本.md 生成 storyboard 并导出作品。`
- `用 vngame 检查这个 H5 能不能上线。`

## 注意

- 这个包不包含真实生产项目素材。
- 压缩图片、COS 上传、图像生成等功能都通过环境变量读取密钥，不要把密钥写进仓库。
