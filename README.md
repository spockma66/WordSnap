# 项目起源

因为不喜欢死记硬背，我一直希望用游戏和看剧等方式，在场景中学习英语单词，以及更地道的表达方式。但遇到了两个痛点，以游戏为例

1. 这是游戏《Warhammer 40,000: Rogue Trader》（下面简称行商浪人）真正开始后的首屏对话![](https://i.imgur.com/i6tD7Be.jpeg) 对我而言，上面的一屏文字有8个生词，查得很辛苦，也影响跟上剧情的节奏
2. 查单词的时候，词典会提供好几种近似解释。要理解整段文字，就得先精准理解上面8个词每个的具体含义，同时又能适当引申，猜得很累

因此，我开发了这个项目，通过树莓派来识别内容，然后点击单词就能看到基于上下文的解释，并听到单词发音。现在我把它开源，希望能帮助有相似需求的人

# 使用场景

- **识别电视文字**
  - 游戏《行商浪人》：对于游戏首屏对话的使用见下图，下方为树莓派输出的10寸触摸屏![](https://i.imgur.com/81S39ES.jpeg) 触摸屏截图，上半部分文字来自识别到的游戏对话![](https://i.imgur.com/MPOc8bm.png)
    - 点上面两个识别区域的任意单词，在下面对应的区域会出现解释。高亮的词是GRE+托福词库内的，来源见最后感谢部分
    - 点下面两个解释区域最后的单词，可以听刚才查询单词的发音
    - 树莓派会持续识别大屏幕的文字，但在树莓派界面上进行任何操作，都会让识别暂停。要再次识别大屏幕上的新内容，点击界面下方的 Resume Image Capture 即可
  - 英文书籍：手机投屏看英文书，书的内容![](https://i.imgur.com/mYUI8Gb.jpeg) 在15.6寸屏幕上，识别的内容和对单词artifacts的解释![](https://i.imgur.com/RA9yzlB.png) 和下方通用词典的artifacts查询结果对比，上面基于上下文的解释更贴近当前场景![](https://i.imgur.com/hCDHpaK.jpeg)
- **识别电脑文字**
  - 游戏《极乐迪斯科》：最初的对话![](https://i.imgur.com/9MMxEZx.jpeg) 触摸屏截图![](https://i.imgur.com/XXm7Oy4.png)
  - 英文视频：猫的故事![](https://i.imgur.com/doCOuKV.jpeg) 触摸屏截图![](https://i.imgur.com/SEwyvSW.png)

# 使用准备

本项目的测试环境主要是 8G 内存的树莓派 5 + 高清摄像头（能拍 1080P 照片）

**硬件准备**

- **烧录系统**：在 [Raspberry Pi 官方网站](https://www.raspberrypi.com/software/)下载 Raspberry Pi Imager，按说明在 TF 卡上安装 Raspberry Pi OS。需要一张几十元的tf卡（常见为64G），和一二十元的读卡器。操作教程很多，请自行搜索
- **机器安装**
  - 重要配件![](https://i.imgur.com/QPyhtJv.jpeg) 上图中主要包括
    - 树莓派5（8G）和机箱，树莓派中已经插入烧录完成的TF卡
    - 10寸触摸屏，由树莓派5供电，通过 HDMI 和 USB 口连接。用它是因为在桌面占用空间小，非触摸屏使用效果相同
    - USB无线键盘
    - USB扬声器
  - 树莓派5和机箱![](https://i.imgur.com/NnXSktl.jpeg) 由于跑大模型使得发热量增加，这次尝试了大机箱，主动散热风扇效果也更好。但并非必须使用它，它本身价格也比普通机箱更高
  - USB 扬声器![](https://i.imgur.com/Rpzwd4P.jpeg) 电商平台购买，比较好找，38元
  - **高清摄像头（能拍摄 1080P 图片）**![](https://i.imgur.com/1YgFmmX.jpeg) 电商平台购买，能实现16倍光学 + 4倍数码变焦，229元。需要仔细找一下，大部分的知名品牌都比较贵
    - 识别电视的摆放要求：通过支架悬空到座位上方，确保跟其他物品都不接触，保证稳定性![](https://i.imgur.com/VMwvuqJ.jpeg) 背面看过去正好对着电视![](https://i.imgur.com/502fZlb.jpeg) 图上使用的这类支架，在电商平台一般百元左右可以买到，属于手机直播支架，加个通用的摄像头转接头就可以
    - 识别电脑的摆放要求：放在座位稍微偏一点儿的地方，高度差不多坐着到眼睛，向下俯拍![](https://i.imgur.com/SOyKlQy.jpeg) 拍摄角度如下（摄像头实拍照片）![](https://i.imgur.com/6ERlHdj.jpeg) 
- **更新系统**：开机后先执行 `sudo apt update`，`sudo apt upgrade`，或者使用系统 UI 的更新功能

**软件准备**

- **基础组件**
  - Python 使用 Raspberry Pi OS 自带的 3.11 版
  - 安装 Ollama：`curl -fsSL https://ollama.com/install.sh | sh`（也可以到官网自行查找安装方式 [ollama.com](https://ollama.com)），然后下载模型到本地：`ollama pull qwen2.5:1.5b`
  - 为了使用 USB 摄像头，还需要安装 fswebcam 和 mplayer，它们会在后面环节发挥作用
    - 强烈建议在测试摄像头前，确认要使用的摄像头的设备路径。先执行 `lsusb` 命令，在 USB 设备中，能看到摄像头名字；然后执行 `v4l2-ctl --list-devices` 命令，显示摄像头对应的几个设备路径，用第一个就行。需要确保，config文件中的usbcam_path，跟实际查出来的设备路径保持一致
    - 安装 mplayer：`sudo apt install mplayer -y`，然后测试。如果设备是 `/dev/video0`，测试时直接执行 `sudo mplayer tv://`。否则加上 `"-tv device=具体设备路径"` 这个参数再运行
    - 安装 fswebcam：`sudo apt install fswebcam -y`，然后测试。如果设备是 `/dev/video0`，测试时直接执行 `fswebcam --no-banner -r 1920x1080 ~/test.jpg`，否则加上 `"-d 具体设备路径"` 这个参数再运行
- **Raspberry Pi OS 默认已有 Git，直接安装项目**
  - **操作流程**
    - `git clone https://github.com/spockma66/WordSnap.git`
    - `cd WordSnap`
    - `python -m venv venv`
    - `source venv/bin/activate`
    - `pip install -r requirements.txt`。如果安装 Python 库太慢，国内有清华大学的源可用，请自行搜索
  - 项目文件中包括 onnx 和可执行文件，便于直接运行。如果希望自己生成，或使用其他版本，可以删除 models 下所有文件，然后
    - 访问 RapidAI 的 [PaddleOCRModelConvert](https://github.com/RapidAI/PaddleOCRModelConvert) 自行生成识别英文的 OCR 模型，并替换 config 文件中的 `ocr_model_path`
    - 访问 Kaldi 语音框架的 [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)，下载基础模型和语音模型，安排好存放位置，然后修改 `tts_config` 中的各个值，这部分可以参考 [哔哩哔哩的视频](https://www.bilibili.com/video/BV1tu4y1H7jD/)。如果使用过程中希望改变语音效果，也请参考该视频

# 开始使用

- 先把 config 文件中的 `current_mode` 值改为 `test` 并保存，然后在虚拟环境中执行 `python main.py`，看拍摄的照片效果如何，包括
  - 对准和对正识别的目标
  - 聚焦清晰
  - 识别出了所有应该识别出的文字，可以看方框覆盖了哪些文字
  - 是否识别出了不需要识别的固定文字。例如，电视下边沿展示的品牌名，会干扰文本分类结果。这些固定文字可以用 config 中的 `black_list` 把它们排除。我用了红米电视，因此我的 `black_list` 值就是 `["Redmi"]`
- 如果发现有问题，可以再次开启 mplayer，调整位置、焦距和亮度等。请注意，mplayer 显示的效果，可能跟 test 模式下拍摄的不一致，但仍然可以放大缩小和调整亮度。最后以 test 模式拍摄效果为准
- 调整结束时，摄像头要放在不容易晃动的地方，保证拍照效果稳定。然后把 config 文件中的 `current_mode` 的值改为 `normal` 并保存
- 在虚拟环境中，执行 `python main.py`，开始使用

# 配置文件简述

- 配置文件位于项目目录下的 `configs` 文件夹中，共有三个。配置项的名称都相对好理解，可以先自行查看，简要介绍如下
- `config` 文件，包括启动和识别文字，再到组织成文本并展示的相关配置。如果使用者说中文以外的语言，修改三个配置项就可以使用
  - `ollama_api` 中，`data` 的 `model`，改为你所使用的语言表现比较好的模型，或者是 `llama 3.2 1B` 这样相对通用的模型，3B 的模型也能运行，但是会有点儿慢
  - `ollama_api` 中，`data` 的 `prompt`，改成用你的语言，让模型解释单词在上下文中的意思，以及常见用法。但 `{word}` 和 `{full_text}` 的写法不能改变
  - `pronunciation_hint`，改为你的语言，提示用户，点击单词可以听到发音
- `ui_config` 文件，包括界面相关的配置
- `tts_config` 文件，是发音模型的启动及语音速度相关的配置

稍后会补充详细的说明

修改配置文件并保存后，请重新启动程序

# FAQ

- **如何使用这个产品？** 按照上述说明，开始使用后，先关注大屏幕上的内容本身。确认了不理解的生词后，再看树莓派的识别结果，并点击具体的词查询。在树莓派界面做任何操作，都会使得对大屏幕持续的识别暂停，这样保证了当前关注的内容不被刷新，点击下方 `Resume Image Capture` 就能继续识别新内容
- **调试摄像头时看起来对焦清晰，但识别出的效果仍然有瑕疵（例如单词之间的空格识别不出来）怎么办？** 可以用 mplayer 打开摄像头，然后用遥控器降低摄像头亮度。只要保证字看起来更清楚，不用在意拍摄到画面的明暗。在拍摄的屏幕有外部强光源（顶灯/台灯）照射时，这个操作尤其有效
- **720p 的 USB 摄像头可以用吗？** 不推荐，我的使用效果不好
- **树莓派官方摄像头可以用吗？** 至少 3 代可以，拍电视效果较好，见下图。但很难拍电脑，CSI 扁线又短又难扭转，无法验证实际效果
  - 使用效果![](https://i.imgur.com/NyJowsO.jpeg) 
  - 摄像头摆放方式。摄像头是官方 camera module 3 wide（289 元），连接线是 50 厘米 CSI 摄像头连接线（29 元）![](https://i.imgur.com/jNvWZHi.jpeg) 
  - 拍摄角度，通过 test 模式获得照片，方框中为识别出的文字![](https://i.imgur.com/fmgV7lQ.png) 
  - 最终识别结果截屏![](https://i.imgur.com/k3s16PI.png) 
- **各种游戏场景的识别效果都很好吗？** 对于动画效果明显，或者字体明暗对比强烈，又或者有很多花体字的游戏界面，例如刚进入游戏时的主菜单，识别效果可能略差
- **听发音时，为什么提示音后会稍作停顿，然后念一句话，而不像常见的词典那样直接念单词？** 因为经过多次尝试，选了一种发音的 medium 版本，耗时更长。如果直接念单词，出现重音不准的概率会增加，推测跟训练材料分布有关
- **会不会偷偷回发数据，或者拍的照片？** 不会，如果不愿意看代码，可以给树莓派断网后再用（要先安装完项目），关闭程序后再恢复网络
- **如果发现了问题，有什么信息可以参考吗？** 严重的摄像头问题界面会有指示。本地项目目录的 `log` 文件夹下，存了最后一次运行的日志，有兴趣可以自己打开，结合代码研究

# 感谢

1. OCR 的识别效果，归功于 [RapidAI](https://github.com/RapidAI/) 和 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
2. 默认的单词解释效果，归功于通义千问的 [Qwen2.5](https://github.com/QwenLM/Qwen2.5) 和 [Ollama](https://ollama.com/)
3. 默认的单词发音效果，归功于 [Kaldi 语音框架](https://github.com/k2-fsa/sherpa-onnx) 和 [Piper](https://github.com/rhasspy/piper)
4. 默认的高亮单词词库，归功于 [mahavivo 的词库列表](https://github.com/mahavivo/vocabulary/tree/master/vocabulary)


