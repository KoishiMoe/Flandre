此处提供的是用于将AnimeThesaurus的词库转换为Flandre词库的脚本，它并不是一个包，目前不为Flandre本体提供任何功能（也许以后会让bot能够自动导入该词库……不过目前还没做）

## 使用方法：
* 去 https://github.com/Kyomotoi/AnimeThesaurus 下载词库`data.json`，并放在该目录下
* 运行该脚本
```console
$ python3 ./convert.py 
```
* 将生成的`output.json`中所有内容复制到你的`wordbank.json`中，并将其至于自定义目录（`data/resources/custom/chat`）下（如果你想让它可以在对话中被操作，也可以将其与`data/database/chat/0.json`合并）

## 注意事项：
* 生成的词库的所有条目均以关键词模式匹配，以纯文本形式回复，其他选项均为默认
