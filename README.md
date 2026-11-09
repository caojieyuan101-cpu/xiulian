# 日语修行

听力 · 阅读 · 口语打卡的离线网页 app（PWA）。装到 iPhone 主屏幕后断网也能用，记录和照片只存在手机上。

- 网站文件在仓库根目录，由 GitHub Pages 发布
- 源码在 `source/`：改 `app.html`、`poems.json`、`sw.js` 后运行 `python3 source/build.py` 重新生成根目录的文件
- 构建需要 `fonttools`、`brotli`、`Pillow`，以及 `npm pack @fontsource/noto-serif-sc@5.1.1` 解压后的字体目录（用环境变量 `FONTDIR` 指定）

## 睡眠记录（`sleep/`）

另一个独立的离线小 app：睡前点“开始睡觉”，醒来点“起床了”，记下睡眠质量、躺下多久睡着、夜醒次数、标签和备注；也能补记、修改、删除。数据只存在手机上，可以导出 / 恢复备份。

- 壁纸：像手机壁纸一样铺在整个 app 后面，自带“教室晚霞”照片和两张渐变，可以从相册导入自己的（存在这台设备的 IndexedDB 里），在设置页或首页右上角切换，用滑动条调虚化程度
- 趋势页：7 天 / 30 天 / 90 天 / 1 年，每晚时长和入睡起床图表，和上一段时间的对比，作息时间范围和准时率，最长最短、睡眠债，星期规律，时长和质量分布，连续记录天数，标签对睡眠的影响
- 数字用系统的圆体粗体（Apple 设备上是 SF Rounded）
- 地址：GitHub Pages 站点下的 `sleep/`，用 Safari 打开后“添加到主屏幕”
- 直接改 `sleep/index.html`，不需要构建；改完把 `sleep/sw.js` 里的 `CACHE` 版本号加一，已安装的手机才会更新
- 图标由 `python3 source/sleep_icons.py` 生成（需要 Pillow）
- 自带的照片 `sleep/bg-classroom.jpg` 来自小红书 @September47_
