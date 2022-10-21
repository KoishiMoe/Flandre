## 新用户注意

本项目目前已经**基本停止开发**，仅为方便老用户使用而保留。虽然本项目的绝大部分功能都是正常可用的（部分功能仍有bug），不过如果你正在寻找一个好用的群bot，基于以下原因，我**不建议**选择本项目。

* 日后我没有时间维护这类项目，因此只会进行最低限度的bug修复，**不会有任何功能更新**，也不会修复一些我平时感受不到的问题
* 这个bot是我在学习阶段的作品，许多地方代码十分杂乱、不符合规范，前后风格也不一致，阅读和维护困难
* 承前所述，开发期间跨度长，不同功能组件在使用上体验也不一致（例如wiki插件以对话式交互为主，后面的功能则主要是类shell命令的语法）
* 命令语法复杂难记（我自己都需要经常查帮助...）
* 设计时只注重功能，考虑比较简单，缺少缓存等机制，**性能较差**，尤其对io差的机器不友好
* 结构比较简单，大部分都是功能拼接，通过市场上现有的插件进行组合可以实现绝大多数功能

当然，如果你喜欢里面的某个功能的话，可以把实现该功能的插件提取出来，一般来说稍加修改后便可以作为一个标准的nonebot2插件使用。如果确有需要的话，也可以提交issue，我可能会将其独立发布。

------

<div align="center">

# Flandre

![Python](https://img.shields.io/badge/python-3.10%2B-lightgrey)
![nonebot2](https://img.shields.io/badge/nonebot2-2.0.0b2-yellowgreen)
[![GitHub license](https://img.shields.io/github/license/KoishiMoe/Flandre)](https://github.com/KoishiMoe/Flandre/blob/main/LICENSE)

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
* 所有参与测试的群友，以及各位用户
