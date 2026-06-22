# 服务器/白名单通用说明

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

- 端口：8080，或通过 `PORT` 环境变量指定的端口。
- 协议：HTTP。
- 来源：本机 localhost、可信局域网设备。
- 目标：开发机 IP 和预览服务端口。

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

## 静态部署建议

生产环境建议采用独立静态路径，例如：

```text
线上 URL: https://{your-domain}/h5/{gameId}/
服务器目录: /path/to/webroot/h5/{gameId}/
入口文件: /path/to/webroot/h5/{gameId}/index.html
```

规则：

- 每个作品使用独立路径，例如 `/h5/{gameId}/`。
- 不要把单个作品直接覆盖站点根路径。
- 不存在的作品路径应返回 404，避免错误回落到旧作品。
- 图片和音频可以与 HTML 一起上传，也可以按项目规范走对象存储/CDN。

Nginx 位置示例：

```nginx
location ^~ /h5/{gameId}/ {
    alias /path/to/webroot/h5/{gameId}/;
    index index.html;
    try_files $uri $uri/ /h5/{gameId}/index.html;
}
```

## 安全规则

- 密码、API key、SecretKey、SSH key 不写入 Markdown 或仓库。
- 服务器 IP、内网域名、真实目录、登录用户等内部信息不要放进公开 skill 包。
- 如需本机读取凭据，使用仅自己可访问的私有文件或环境变量。
