# ErTing - AI 音频/视频降噪工具

一款基于 AI 的本地音频/视频降噪工具。ErTing 使用 ModelScope 的语音增强模型，从您的音频和视频文件中去除噪声，输出干净、专业的音质。

> **ErTing (耳听)** -- 听得清。

![Web 界面](images/web.png)

## 功能特性

### 三种使用方式

- **命令行** - 功能完整的命令行界面，支持统一参数标志
- **桌面 GUI** - PySide6 桌面应用，支持批量处理、多文件和目录导入
- **Web 界面** - 基于 Flask 的网页界面，浏览器中即可使用

### 核心能力

- 基于 ModelScope 模型的 AI 降噪
- 支持多种音频/视频格式（MP3、WAV、MP4、AVI、MOV、M4A、FLAC、OGG、WMA、AAC）
- 自动转换为 16kHz WAV 格式进行最优处理
- 可配置输出路径和模型选择
- JSON 输出支持自动化工作流

## 截图

| GUI（批量处理） | Web 界面 |
|:--------------:|:--------:|
| ![GUI](images/gui.png) | ![Web](images/web.png) |

## 环境要求

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/)（用于音频格式转换）
- [ModelScope](https://modelscope.cn/) 包
- 建议 2GB+ 内存用于模型加载

## 安装

### 方式一：从 PyPI 安装

```bash
pip install erting
```

### 方式二：从源码安装

```bash
git clone https://github.com/cycleuser/ErTing.git
cd ErTing
pip install -e .
```

## 快速开始

### 命令行用法

```bash
# 基础降噪
erting input.mp3

# 指定输出路径
erting -o output_clean.wav input.mp3

# JSON 输出（适合脚本）
erting --json input.mp3

# 详细模式
erting -v input.mp3

# 静默模式（最少输出）
erting -q input.mp3
```

### GUI 用法

```bash
erting-gui
```

GUI 支持：
- **添加文件** - 一次选择多个音频/视频文件
- **添加目录** - 导入文件夹中所有支持的音频文件
- **批量处理** - 按顺序处理所有文件，带进度跟踪
- **自动命名** - 输出文件默认命名为 `{原文件名}_clean.wav`
- **自定义输出目录** - 选择独立的输出文件夹
- **停止/恢复** - 处理中途可取消

### Web 界面

```bash
erting-web
```

然后在浏览器中打开 [http://localhost:5001](http://localhost:5001)。

## 命令行参数

```
erting [-V] [-v] [-o PATH] [--json] [-q] input [options]

位置参数：
  input                  输入的音频/视频文件路径

选项：
  -V, --version         显示版本号并退出
  -v, --verbose         启用详细输出
  -o, --output PATH     输出文件路径
  --json                以 JSON 格式输出结果
  -q, --quiet           抑制非必要输出
  --model MODEL         ModelScope 模型名称（默认：iic/speech_zipenhancer_ans_multiloss_16k_base）
```

## Python API

```python
from erting.api import denoise_audio, ToolResult

result = denoise_audio(input_path="input.mp3")
print(result.success)    # True / False
print(result.data)      # {'input_path': ..., 'output_path': ...}
print(result.metadata)  # {'version': '0.1.0', 'model': ...}
```

## Agent 集成（OpenAI 函数调用）

ErTing 提供兼容 OpenAI 的工具供 LLM Agent 调用：

```python
from erting.tools import TOOLS, dispatch

# 将 TOOLS 传入 OpenAI 聊天完成 API
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=TOOLS,
)

# 分发工具调用
result = dispatch(
    tool_call.function.name,
    tool_call.function.arguments,
)
```

## 支持的格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| WAV | .wav | 直接处理 |
| MP3 | .mp3 | 直接处理 |
| MP4 | .mp4 | 提取音频 |
| AVI | .avi | 提取音频 |
| MOV | .mov | 提取音频 |
| M4A | .m4a | 直接处理 |
| FLAC | .flac | 直接处理 |
| OGG | .ogg | 直接处理 |
| WMA | .wma | 直接处理 |
| AAC | .aac | 直接处理 |

## 项目结构

```
ErTing/
├── pyproject.toml              # 包元数据和构建配置
├── requirements.txt            # 依赖列表
├── README.md                   # 英文文档
├── README_CN.md                # 中文文档
├── LICENSE                     # GPL-3.0-or-later
├── upload_pypi.sh              # 自动版本递增的 PyPI 上传脚本
├── upload_pypi.bat             # Windows PyPI 上传脚本
├── erting/
│   ├── __init__.py             # 包版本
│   ├── __main__.py             # python -m erting 入口
│   ├── core.py                 # 音频处理引擎
│   ├── cli.py                  # 统一参数命令行
│   ├── gui.py                  # PySide6 批量 GUI
│   ├── web.py                  # Flask Web 应用
│   ├── api.py                  # ToolResult API
│   ├── tools.py                # OpenAI 函数调用工具
│   └── templates/
│       └── index.html           # Web 界面模板
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # 测试夹具
│   ├── test_core.py            # 核心模块测试
│   ├── test_api.py              # API 测试
│   ├── test_tools.py           # 工具架构测试
│   └── test_cli.py             # CLI 集成测试
├── images/
│   ├── gui.png                 # GUI 截图
│   └── web.png                 # Web 界面截图
└── scripts/
    ├── publish.sh               # PyPI 发布脚本
    └── publish.bat              # Windows 发布脚本
```

## 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_api.py -v

# 运行并生成覆盖率报告
python -m pytest tests/ --cov=erting --cov-report=term-missing
```

## 发布到 PyPI

```bash
# Linux/macOS
./upload_pypi.sh

# Windows
upload_pypi.bat
```

或手动操作：

```bash
rm -rf dist/
python -m build
twine upload dist/*
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
python -m pytest tests/ -v

# 格式化代码
ruff format .

# 代码检查
ruff check .

# 类型检查
mypy erting/
```

## 许可证

GPL-3.0-or-later。详见 [LICENSE](LICENSE) 文件。
