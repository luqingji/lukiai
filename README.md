# 每日宝箱

一个包含102个趣味/知识模块的每日更新网页，核心功能：
- 每日一曲（根据IP地域推荐歌曲，附带歌曲鉴赏）
- 冷笑话、每日一言、诗词、网易热评、名人名言、成语接龙、谚语等网络模块
- 94个内置知识模块（成语、歇后语、历史、科学、心理等）

## 自动更新机制
- GitHub Actions 每天凌晨2点运行爬虫，抓取歌曲鉴赏信息并生成 `song_reviews.json`
- 前端页面从 GitHub raw 读取该 JSON 文件，显示最新歌曲鉴赏

## 部署
1. 将本仓库设置为 GitHub Pages（Settings → Pages → 选择 main 分支，/root 目录）
2. 访问 `https://luqingji.github.io/lukiai` 即可使用

## 自定义
- 如需修改歌曲列表，请编辑 `song_crawler.py` 中的 `SONG_LIST`
- 如需添加更多地区歌曲，请在 `index.html` 的 `regionSongLib` 中补充