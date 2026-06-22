# 服务器/白名单说明

本地和内网预览需要 HTTP 服务，不使用 `file://`。

## 默认服务

```bash
python3 tools/storyboard_server.py
```

默认访问：

```text
http://localhost:8080/storyboard.html
http://localhost:8080/demo.html
http://localhost:8080/作品.html
```

手机局域网访问示例：

```text
http://{开发机IP}:8080/storyboard.html
http://{开发机IP}:8080/作品.html
```

## 运维放通项

- 端口：8080
- 协议：HTTP
- 来源：本机 localhost、局域网设备
- 目标：开发机 IP:8080

## 需要访问的路径

```text
GET  /storyboard.html
GET  /demo.html
GET  /作品.html
GET  /dist/assets/*
GET  /Audio/*
GET  /api/story
POST /api/story
POST /api/export-work
POST /api/assets
POST /api/audio
GET  /api/audio-list
```

## C机（新 vn-studio）部署建议

服务器：

- 别名：`vn-studio-c`
- 公网 IP：`43.138.43.211`
- 内网域名：`dqd-tx-bj8-ldy-web01.dqd.local`
- 当前探测：80/443 已开放，HTTPS 后面是 `nginx/1.20.1 + Next.js`
- 当前限制：本机暂不能解析 `.local` 域名，应优先用公网 IP 或 SSH 别名

### 2026-06-16 后默认 H5 发布域名

新部署的 H5 作品默认走独立 H5 域名，不再继续新增到 `vnstudio.aisportsapp.com`：

```text
线上 URL: https://h5.aisportscfg.com/h5/{gameId}/
服务器目录: /data/www/aisportscfg.com/h5/{gameId}/
入口文件: /data/www/aisportscfg.com/h5/{gameId}/index.html
```

规则：

- 每个作品必须有独立后缀路径，例如 `/h5/fodejiao/`，不要把作品直接放在域名根路径。
- 根路径 `https://h5.aisportscfg.com/` 只允许跳转到当前默认作品或后续作品索引页，不作为作品正式投放链接。
- 新增作品时复用同一个 Nginx server，上传到 `/data/www/aisportscfg.com/h5/{gameId}/index.html` 即可；不存在的作品路径应返回 404，避免错误回落到某个旧作品。
- HTTPS 证书已由 Certbot 部署在 `h5.aisportscfg.com`，证书自动续期；新增路径不需要重新签证书。

H5 游戏不要覆盖站点根路径。推荐让 Nginx 单独截静态子路径。默认采用 **HTML only + COS 素材** 模式。

以下是旧 `vnstudio.aisportsapp.com` 路径，仅作为历史项目参考；新项目不要再按这个域名新增：

```text
线上 URL: https://vnstudio.aisportsapp.com/h5/game10mbappe/
服务器目录: /data/www/h5/game10mbappe/
```

部署文件：

```text
/data/www/h5/game10mbappe/index.html
```

`index.html` 由本地 `作品.cos.html` 复制/重命名而来。图片和音频不上传服务器，继续请求 COS URL。

Nginx 位置建议：

```nginx
location ^~ /h5/game10mbappe/ {
    alias /data/www/h5/game10mbappe/;
    index index.html;
    try_files $uri $uri/ /h5/game10mbappe/index.html;
}
```

说明：

- `/h5`、`/games`、`/vn` 当前都会被 Next.js 接管并返回 404，不适合直接丢文件。
- 需要 Nginx location 放在 Next.js 反代规则之前。
- 密码、API key、SecretKey 不写入 Markdown；如需本机读取，使用仅自己可访问的私有文件或环境变量。

## A机部署状态

服务器：

- 别名：`vn-server-a`
- 公网 IP：`62.234.211.93`
- 用户：`root`
- 主机名：`dqd-tx-bj8-ldy-web00.dqd.local`
- 当前探测：80/443 已开放，返回 `OpenWS`
- SSH：可用，root 可登录
- rsync：可走 SSH；873 端口可连但不返回可用模块，不作为首选

结论：

- A机目前是已有 H5 静态站点服务器，默认 Web 根目录是 `/var/www/h5`。
- 适合按现有结构新增目录式 H5 项目，例如 `/var/www/h5/{gameId}/index.html`。
- 当前不建议改 Nginx/OpenWS 主配置，优先复用默认静态根目录。

现有结构示例：

```text
/var/www/h5/index.html
/var/www/h5/demo1/index.html
/var/www/h5/game6mldn/index.html
/var/www/h5/sanguo/index.html
/var/www/h5/image2-skills/
```

已知域名/站点：

```text
gaokao.aisportsapp.com -> /var/www/gaokao
默认站点 _ -> /var/www/h5
```

如果临时在 A机验证本项目，建议路径：

```text
/var/www/h5/game10mbappe/index.html
https://62.234.211.93/game10mbappe/
```

注意：2026-06-08 曾试上传 `index.html` 到 `/var/www/h5/game10mbappe/index.html`，但用户随后要求“不用部署”，因此该路径只视为一次探测遗留，不作为正式发布入口。
