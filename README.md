# 日语修行

听力 · 阅读 · 口语打卡的离线网页 app（PWA）。装到 iPhone 主屏幕后断网也能用，记录和照片只存在手机上。

- 网站文件在仓库根目录，由 GitHub Pages 发布
- 源码在 `source/`：改 `app.html`、`poems.json`、`sw.js` 后运行 `python3 source/build.py` 重新生成根目录的文件
- 构建需要 `fonttools`、`brotli`、`Pillow`，以及 `npm pack @fontsource/noto-serif-sc@5.1.1` 解压后的字体目录（用环境变量 `FONTDIR` 指定）
