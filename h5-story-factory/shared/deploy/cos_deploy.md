# COS 部署规则

## 上传范围

每个作品上线至少上传：

```text
作品.html
dist/assets/
Audio/
```

## 建议路径

```text
h5/{gameId}/作品.html
h5/{gameId}/dist/assets/*
h5/{gameId}/Audio/*
```

## 部署前

- 先导出最新 `作品.html`。
- 先跑素材引用检查。
- 图片压缩和未引用素材清理已完成。
- 不上传备份目录和本地报告，除非需要归档。

## 部署后

- 打开线上 URL。
- 检查首屏、前 5 帧、一个 choice、一个 gacha、ending。
- 确认音频路径和图片路径都走相对路径。
