# 011 视频文字替换与翻译 / Video Text Replacement and Translation

> 把视频画面中的文字检测、翻译、覆盖和导出串成一条桌面工作流。
>
> **English:** A desktop workflow that detects, translates, covers, and exports text embedded in video frames.

## 解决什么问题 / Problem

烧录字幕或画面文字难以批量替换，翻译后还容易破坏原画面布局。

**English:** Burned-in subtitles and on-screen text are hard to replace in batches, and translation can damage the original layout.

## 项目展示 / Demo

~~~mermaid
flowchart LR
 A[视频输入] --> B[画面文字检测]
 B --> C[翻译 / 文本校正]
 C --> D[覆盖与渲染]
 D --> E[新视频导出]
~~~

从视频输入到新文件导出，保留画面并把文字处理步骤显式化。

**English:** The workflow keeps the video image while making text detection, translation, and rendering explicit.

## 高光亮点 / Highlights

- 桌面端视频处理流程。
  **English:** Desktop video-processing workflow.
- 文字识别、翻译和覆盖串联。
  **English:** Chains OCR, translation, and overlay.
- 保留视频画面并输出新文件。
  **English:** Preserves the video image and exports a new file.
- 前后端脚本可继续扩展。
  **English:** The frontend/backend scripts are extendable.

## 技术名词 / Tech

`Python · JavaScript · FFmpeg · OCR · Translation API · Node.js`

## 从 ZIP 开始复现 / Reproduce from ZIP

1. 解压 ZIP，安装 `requirements.txt` 和 `package.json` 中的依赖。
2. 按项目根目录脚本启动前端/后端。
3. 选择测试视频，设置语言和输出目录。
4. 检查识别文字、翻译结果和导出视频。

**Expected result:** 完成上述步骤后，应能看到项目的页面、窗口、设备输出或测试结果。

**Expected result:** After these steps, you should see the project's page, window, device output, or test result.

## 范围与安全 / Scope and Safety

翻译接口和 FFmpeg 属于运行条件；视频内容、第三方 API Key 和输出文件应使用自己的测试资料。

**English:** The translation API and FFmpeg are runtime requirements; use your own test videos, API keys, and output directory.

## 交流 / Contact

欢迎交流技术。

Open to technical exchange.

[English full version](README.en.md)
