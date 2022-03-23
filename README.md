# Flandre

![Python](https://img.shields.io/badge/python-3.10%2B-lightgrey)
![nonebot2](https://img.shields.io/badge/nonebot2-2.0.0b2-yellowgreen)
[![GitHub license](https://img.shields.io/github/license/KoishiStudio/Flandre)](https://github.com/KoishiStudio/Flandre/blob/main/LICENSE)
[![Chat](https://img.shields.io/badge/Chat-724678572-green)](https://jq.qq.com/?_wv=1027&k=z75kmJl7)
[![DOCS](https://img.shields.io/badge/DOCS-Flandre%20Docs-blue)](https://wiki.koishichan.top/wiki/Flandre:%E5%B8%AE%E5%8A%A9)

[![GitHub issues](https://img.shields.io/github/issues/KoishiStudio/FLandre)](https://github.com/KoishiStudio/Flandre/issues)
[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/KoishiStudio/Flandre?include_prereleases)](https://github.com/KoishiStudio/Flandre/releases)
[![GitHub all releases downloads](https://img.shields.io/github/downloads/KoishiStudio/Flandre/total)](https://github.com/KoishiStudio/Flandre/releases)
![GitHub contributors](https://img.shields.io/github/contributors/KoishiStudio/Flandre)
![GitHub Repo stars](https://img.shields.io/github/stars/KoishiStudio/Flandre?style=social)


基于[nonebot2](https://github.com/nonebot/nonebot2)的机器人（咕咕中……)

项目名称来自 [东方Project](https://zh.moegirl.org.cn/zh-cn/%E4%B8%9C%E6%96%B9Project) 的 [芙兰朵露·斯卡蕾特](https://zh.moegirl.org.cn/%E8%8A%99%E5%85%B0%E6%9C%B5%E9%9C%B2%C2%B7%E6%96%AF%E5%8D%A1%E8%95%BE%E7%89%B9) ，二妹赛高！

~~（其实我是[恋](https://zh.moegirl.org.cn/zh-cn/%E5%8F%A4%E6%98%8E%E5%9C%B0%E6%81%8B)厨的说）~~

目前我还在学习阶段，因此可能更新较慢，功能以及代码质量上都有相当不足，还请多多几教～

另：项目以AGPL-3.0授权

文档请见[我的Wiki](https://wiki.koishichan.top/wiki/Flandre:%E5%B8%AE%E5%8A%A9)以及bot代码内置的帮助文档，后续有时间时会同步到github（发出了鸽子的声音

## TODO
- [ ] 关键词自动回复
  - [ ] 对部分关键词设置仅'@bot'才会触发
  - [ ] 允许群管对本群设置自定义条目（优先级高于自带词库）或关闭部分条目
- [ ] 搜图
  - [ ] Saucenao
  - [ ] Ascii2d
- [x] Wiki推送
  - [x] 调用wiki api
  - [x] URL拼接
  - [x] 多wiki支持
  - [x] 默认wiki设置
  - [x] 各群独立设置
  - [x] 重定向支持
  - [x] 消歧义页支持
- [x] 帮助系统
  - [x] 调用官方wiki内容 （便于实时获取更新）
  - [x] 接入[nonebot-plugin-help](https://github.com/XZhouQD/nonebot-plugin-help) （适用于定制以及网络不好的情况）
- [ ] 群管系统
  - [ ] 全局拉黑
  - [ ] 自动禁言
  - [ ] 欢迎
- [ ] Bot管理
  - [ ] 好友验证/群验证
  - [ ] 禁用/启用功能
  - [ ] 禁言状态检测、休眠
  - [ ] 错误报告
  - [ ] 运行状态获取
  - [ ] 反馈系统
  - [x] 撤回bot消息（由于上游bug,暂不支持分片消息撤回）
- [x] 小程序处理
  - [x] （伪）通用
  - [x] 屑站专用解析
- [ ] 涩图
- [ ] 小工具
  - [x] pixiv图片获取
  - [ ] 在线运行代码
  - [ ] 骰子
  - [x] http.cat
  - [x] 快速搜索
