# Flandre

基于[nonebot2](https://github.com/nonebot/nonebot2)的机器人（咕咕中……)

项目名称来自 [东方Project](https://zh.moegirl.org.cn/zh-cn/%E4%B8%9C%E6%96%B9Project) 的 [芙兰朵露·斯卡蕾特](https://zh.moegirl.org.cn/%E8%8A%99%E5%85%B0%E6%9C%B5%E9%9C%B2%C2%B7%E6%96%AF%E5%8D%A1%E8%95%BE%E7%89%B9) ，二妹赛高！

~~（其实我是[恋](https://zh.moegirl.org.cn/zh-cn/%E5%8F%A4%E6%98%8E%E5%9C%B0%E6%81%8B)厨的说）~~

目前我还在学习阶段，因此可能更新较慢，功能以及代码质量上都有相当不足，还请多多几教～

另：项目以AGPL-3.0授权

## TODO
- [ ] 关键词自动回复
  - [ ] 对部分关键词设置仅'@bot'才会触发
  - [ ] 允许群管对本群设置自定义条目（优先级高于自带词库）或关闭部分条目
- [ ] 搜图
  - [ ] Saucenao
  - [ ] Ascii2d
- [ ] ~~AI鉴黄（使用deepdanbru）（用于bot对自己要发送的图片进行预检测）~~ （性能原因暂时放弃）
- [x] Wiki推送
  - [x] 调用wiki api
  - [x] URL拼接
  - [x] 多wiki支持
  - [x] 默认wiki设置
  - [x] 各群独立设置
- [x] 帮助系统
  - [x] 调用官方wiki内容 （便于实时获取更新）
  - [ ] 接入[nonebot-plugin-help](https://github.com/XZhouQD/nonebot-plugin-help) （适用于定制以及网络不好的情况）
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
  - [ ] 屑站专用解析
- [ ] 涩图
- [ ] 小工具
  - [x] pixiv图片获取
  - [ ] 在线运行代码
  - [ ] 骰子
  - [ ] http.cat