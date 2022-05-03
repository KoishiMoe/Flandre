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


基于 [nonebot2](https://github.com/nonebot/nonebot2) 的机器人（咕咕中……）

项目名称来自 [东方Project](https://zh.moegirl.org.cn/zh-cn/%E4%B8%9C%E6%96%B9Project) 的 [芙兰朵露·斯卡蕾特](https://zh.moegirl.org.cn/%E8%8A%99%E5%85%B0%E6%9C%B5%E9%9C%B2%C2%B7%E6%96%AF%E5%8D%A1%E8%95%BE%E7%89%B9) ，二妹赛高！

~~不过这个项目的功能目前和二妹似乎还没啥关系（逃）~~

bot代码内有帮助文档，在运行时也可以用`help`命令查看帮助文档

## 部署

**注意：**

**1. Flandre目前只适配了cqhttp的反向websocket连接方式，如果需要其他连接方式，可以手动修改bot源码～**

**2. Flandre只适配了`Onebot V11`，请勿使用`mirai`、钉钉等**

**3. 自v0.4.0起，Flandre将使用`poetry`管理项目依赖。`requirements.txt`仍将被提供，但是是由poetry自动生成，因此推荐使用poetry进行安装和更新**


### 1. 下载bot
#### 使用git
```console
$ git clone https://github.com/KoishiMoe/Flandre 
```
#### 不使用git
你可以点击右上角的`Code`-`Download ZIP`来获取主分支的zip压缩包，并把它解压到你想要的目录；或者也可以在右侧的`Release`处下载（不过更新并不及时）

### 2. 安装bot
首先你要有`Python`（废话），不过由于`Flandre`使用了一些新语法，因此需要`3.10`及以上的版本，还请留意

以下步骤将使用`poetry`进行依赖的安装，如果你还没有安装`poetry`，可以按照下面的方法安装：

osx / linux / bashonwindows：
```console
$ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
windows powershell：
```powershell
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -
```

首先，切换到bot文件所在的目录。**请不要将bot的文件解压到诸如“下载”之类的公共目录，否则bot运行产生的文件可能造成混乱，并且不利于后续的更新**

然后，在你的shell中，执行：
```console
$ poetry install --no-dev
```

稍等一会后依赖即可安装完成。如果报错，请尝试在搜索引擎查找。如果确定是本项目的问题（例如提示依赖冲突），可以提交issue（注意附上错误报告）

然后使用下面的命令来运行bot：
```console
$ poetry run python bot.py
```

首次启动bot会生成`config.yaml`，按注释内容填写后，再次运行即可启动。

以后再启动bot,只需要切换到bot所在的目录，并执行上面**最后一条**命令即可

<details>
  <summary>旧版教程：不使用`poetry`进行安装</summary>

  如果你不愿意使用poetry,也可以直接使用pip进行安装。不过下面的内容可能不会再更新，还请留意。
  
  为了降低维护成本以及减少冲突，我们推荐使用python的虚拟环境来运行
  
  先创建一个虚拟环境，在bot根目录下执行：
  ```console
  $ python -m venv venv
  ```
  然后进入虚拟环境：
  ```console
  $ source venv/bin/activate
  ```
  
  此时你的shell可能会有相应的显示，不过没有也没关系
  
  如果你的电脑上有多个python版本，此时建议检查一下python版本
  ```console
  $ python --version
  ```
  
  如果输出`Python 3.10.x`或更高版本就可以，否则你需要重新使用对应版本来创建虚拟环境
  
  然后再安装依赖：
  ```console
  $ pip install -r requirements.txt
  ```
  
  在中国大陆，由于某些原因可能无法正常下载，此时可以使用国内镜像来安装：
  
  ```console
  $ pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
  ```
  
  安装完成后，直接在当前目录执行：
  ```console
  $ python ./bot.py
  ```

首次启动以及更新后会生成一个配置文件`config.yaml`，按内部的注释填写相应值即可

以后启动时，如果没有新的依赖的话，就只需要进入虚拟环境后执行上述命令即可。如果报错导入失败，则可能需要重新安装/更新依赖

</details>

### 3. 安装go-cqhttp

（理论上使用`Onebot-Kotlin`可以让她和`mirai`插件一起工作，不过我并未进行测试，无法保证兼容性；
如果出现问题，请在提交issue前先尝试使用`go-cqhttp`检查是否有相同问题）

1. 前往[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)下载
2. 运行`go-cqhttp`，按照提示生成初始配置文件（**注意连接方式选择`反向Websocket`**）
3. 修改配置文件，填写好用户名、密码等，`ws-reverse`下的`universal`后填写 `ws://localhost:8080/onebot/v11/ws`
4. 其他配置一般无须更改，如果担心bot风控问题，可以尝试修改`device.json`（风控比较玄学……）
5. 再次启动`go-cqhttp`，不出意外的话应该可以正常登陆并连接到bot了，同时bot一端也会有连接提示。大功告成！
6. **如果在部署`go-cqhttp`的过程中出现了问题，请去查看`go-cqhttp`的文档以及issue，如非确定是本bot导致的问题，请不要在本项目提相关issue**

### 4. 切换通道以及更新

#### 使用git
如果你当初是使用`git clone`下载和安装的bot,那么后续切换通道以及更新将会很容易。

下面所有操作都应当在bot根目录中执行

##### 更新
```console
$ git pull
```
Tip:如果提示`your local change will be overwritten...`之类，说明本次更新内容与你对代码文件的修改有冲突，此时你可以撤销你的本地更改并再次尝试拉取，不过个人建议按照下面不使用git的方式来更新，以免出现意外

更新后建议更新一下依赖：
```console
$ poetry install
```

再次运行bot，此时更新已经完成。有时bot更新会向配置文件增加新的配置项，此时bot会备份旧的配置文件到`config.yaml.bak`，并转移原有配置到`config.yaml`，然后自动退出，并提示你编辑配置文件。由于读写yaml的库的限制，更新后的配置文件会缺少一些注释，建议对照`config_default.yaml`进行填写。

##### 切换通道（以切换到dev为例）
```console
$ git switch dev
```
对旧版git
```console
$ git checkout dev
```
（实际上就是切换分支）

#### 不使用git
当你无法使用git更新（例如冲突，或者部署时直接下载的zip）时，可以采取下面的方案

##### 更新
按原来的方法下载zip包，解压到新的目录，然后复制原目录中的`data`目录、`config.yaml`文件到新目录，再按`安装bot`中的方式安装依赖

##### 切换通道
在页面左上角，点击`main`按钮，选择要切换到的分支，然后点击右侧的`Code`-`Download ZIP`，再按上面的更新步骤进行配置的转移

### 5. 使用第三方插件
```plaintext
注意：由于`Flandre`的管理系统与插件见存在一定程度的整合，使用第三方插件可能出现一些问题，例如无法使用服务管理器开关、命令冲突、存储冲突等，请谨慎使用。如有必要，建议在插件的协议允许的范围内手动进行一定的适配，适配方法可以参考内置插件
```

由于本项目依赖git进行部署和更新，如果直接修改bot的插件配置，可能会导致更新时出现冲突。因此，`Flandre`内建了加载第三方插件的功能

操作方法很简单：首次启动后，bot会在根目录生成`plugins.json`，在`src`目录下生成`third_party_plugins`，二者均会被git忽略，因此可以放心修改

如果需要加载来自pypi的第三方插件，只需在`plugins.json`内的`plugins`内填入相应插件名称（记得用双引号括起来，多个则用逗号分隔）；如果要加载以文件或目录形式提供的~~散装~~插件，直接将其复制到`src/third_party_plugins`目录内即可


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
  - [x] 接入[nonebot-plugin-help](https://github.com/XZhouQD/nonebot-plugin-help)
- [ ] 群管系统
  - [ ] 全局拉黑
  - [ ] 自动禁言
  - [ ] 欢迎
- [x] Bot管理
  - [x] 好友验证/群验证
  - [x] 禁用/启用功能
  - [x] 禁言状态检测、休眠
  - [x] 错误报告
  - [x] 运行状态获取
  - [x] 反馈系统
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
