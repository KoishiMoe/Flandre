## 跑路啦，跑路啦

懒得维护了，屎山重构要命

而且以后确实没什么时间写这些玩意了QWQ

如果感兴趣的话，欢迎fork，fork之后你就可以随意~~调♂教~~她了，遵守AGPLv3协议即可

以后还有可能继续更新吗？Maybe…也许哪天我心情好了，或者闲的发慌了，或者心情不好了，会想起来这个也说不定(笑)

------

<div align="center">

# Flandre

![Python](https://img.shields.io/badge/python-3.10%2B-lightgrey)
![nonebot2](https://img.shields.io/badge/nonebot2-2.0.0b2-yellowgreen)
[![GitHub license](https://img.shields.io/github/license/KoishiMoe/Flandre)](https://github.com/KoishiMoe/Flandre/blob/main/LICENSE)
[![Chat](https://img.shields.io/badge/Chat-724678572-green)](https://jq.qq.com/?_wv=1027&k=z75kmJl7)

[![GitHub issues](https://img.shields.io/github/issues/KoishiMoe/FLandre)](https://github.com/KoishiMoe/Flandre/issues)
[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/KoishiMoe/Flandre?include_prereleases)](https://github.com/KoishiMoe/Flandre/releases)
[![GitHub all releases downloads](https://img.shields.io/github/downloads/KoishiMoe/Flandre/total)](https://github.com/KoishiMoe/Flandre/releases)
![GitHub contributors](https://img.shields.io/github/contributors/KoishiMoe/Flandre)
![GitHub Repo stars](https://img.shields.io/github/stars/KoishiMoe/Flandre?style=social)

</div>

-----

基于 [nonebot2](https://github.com/nonebot/nonebot2) 的机器人（咕咕中……）

项目名称来自 [东方Project](https://zh.moegirl.org.cn/zh-cn/%E4%B8%9C%E6%96%B9Project) 的 [芙兰朵露·斯卡蕾特](https://zh.moegirl.org.cn/%E8%8A%99%E5%85%B0%E6%9C%B5%E9%9C%B2%C2%B7%E6%96%AF%E5%8D%A1%E8%95%BE%E7%89%B9) ，二妹赛高！

~~不过这个项目的功能目前和二妹似乎还没啥关系（逃）~~

bot代码内有帮助文档，在运行时也可以用`help`命令查看帮助文档

## 部署
请参考[Wiki的对应页面](https://github.com/KoishiMoe/Flandre/wiki/%E9%83%A8%E7%BD%B2)

## 功能
**鉴于最近的一些情况，暂时不会开发可以涩涩的功能**
- [x] 将bot输出的长文本转换成图片，防刷屏
- [x] 关键词自动回复
  - [x] 对部分关键词设置仅'@bot'才会触发
  - [x] 允许群管对本群设置自定义条目或关闭部分条目
- [ ] ~~搜图~~
  - [ ] ~~Saucenao~~
  - [ ] ~~Ascii2d~~
- [x] 点歌（网易云、Q音）
- [x] Wiki推送
- [x] 帮助系统
  - [x] 接入[nonebot-plugin-help](https://github.com/XZhouQD/nonebot-plugin-help)
- [ ] 群管系统
  - [x] 支持将多个群绑定为群组并共享部分设置，提高多群管理效率
  - [x] 黑白名单
  - [ ] 自动禁言
  - [x] 进群欢迎/退群提示
  - [x] 群组广播
  - [x] 群名片格式检查
  - [x] 进群问题审核
- [x] Bot管理
  - [x] 好友验证/群验证
  - [x] 删除好友/退群
  - [x] 禁用/启用功能
  - [x] 封禁用户（禁止加好友，并且对其禁用全部功能）
  - [x] 禁言状态检测、休眠
  - [x] 错误报告
  - [x] 运行状态获取
  - [x] 登入、登出提示
  - [x] 反馈系统
  - [x] 频率限制（可高度自定义）
  - [x] 撤回bot消息（由于上游bug,暂不支持分片消息撤回）
  - [x] 全局消息随机延迟
- [x] 小程序处理
- [x] 屑站分享解析
- [ ] ~~涩图~~
- [x] pixiv图片获取
- [ ] 在线运行代码
- [ ] 骰子
- [x] http.cat
- [x] 快速搜索
- [x] 一言
- [x] MC服务器监测
- [x] 复读姬
- [x] 服务管理器（支持对人、对群、全局等）

## 致谢
* [nonebot2](https://github.com/nonebot/nonebot2) 项目框架
* [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) 稳定、强大的CQHTTP实现
* [ATRI](https://github.com/Kyomotoi/ATRI) 本项目最初的动力来源，也为本项目提供了大量的参考
* [Bison](https://github.com/felinae98/nonebot-bison) 早期参考
* [nonebot_plugin_analysis_bilibili](https://github.com/mengshouer/nonebot_plugin_analysis_bilibili) b23extract插件参考了其部分代码
* [nonebot_plugin_help](https://github.com/XZhouQD/nonebot-plugin-help) 本项目的帮助系统即为该插件的修改版
* [nonebot_plugin_withdraw](https://github.com/MeetWq/nonebot-plugin-withdraw) 本项目撤回插件即为其改版
* [nonebot_plugin_txt2img](https://github.com/mobyw/nonebot-plugin-txt2img) 文本转图片参考
* 所有参与测试的群友，以及提供反馈、支持和鼓励的各位
