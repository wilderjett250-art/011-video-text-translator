# 011 Video Text Translator / 视频字幕替换翻译桌面工具

Video Text Translator 是一个面向 Windows 的桌面软件项目，用于把视频中已经烧录到画面里的外语文字，替换成新的翻译叠加文本，并导出新的 MP4 文件。

这个项目采用“桌面壳 + 网页操作台 + 本地视频引擎”的组合结构：Electron 负责桌面入口，React 负责操作界面，Python 负责视频处理、项目存储、OCR/翻译适配和导出流程。

## 项目定位

- 项目编号：011
- 项目类型：桌面应用 / 本地视频处理工具
- 使用场景：字幕替换、视频本地化、外语视频内容二次编辑
- 运行平台：Windows
- 主要技术栈：
  - Electron
  - React
  - TypeScript
  - Vite
  - FastAPI
  - Python
  - OpenCV / Pillow / FFmpeg 适配

## 核心能力

- 从本地路径或浏览器上传创建项目
- 解析源视频并提取预览帧
- 以项目形式保存编辑状态
- 基于矩形区域定义原文覆盖和译文显示位置
- 本地生成新的 MP4 输出文件
- 保留原始源视频，不直接覆盖输入文件
- 音频存在时保留音轨并完成重新封装
- OCR 与翻译能力采用适配器方式组织，便于后续切换不同服务

## 目录结构

```text
apps/
  client/                 React 操作界面
  desktop/                Electron 桌面壳
backend/
  app/                    FastAPI 服务与视频处理逻辑
runtime/
  projects/               本地项目运行目录，占位符已保留
scripts/
  start-dev.ps1           开发模式启动脚本
  start-desktop.ps1       桌面模式启动脚本
package.json              前端工作区脚本
requirements.txt          Python 依赖
```

## 架构说明

这个项目的实现思路比较清晰，核心是把“操作界面”和“视频引擎”分离：

1. React 前端负责项目导入、区域选择、参数编辑和任务触发。
2. Electron 提供桌面容器，让整个工具以本地软件方式运行。
3. FastAPI 后端提供本地 API，负责视频探测、帧处理、项目持久化和导出任务。
4. OCR 与翻译逻辑做成适配层，后续接入 PaddleOCR、商业翻译接口或其他本地模型时，不需要重写编辑器主体。

这种结构的好处是：

- 界面迭代和视频处理逻辑彼此解耦
- 本地运行，隐私边界更清楚
- 适合后续继续扩展 OCR、翻译和导出策略
- 对单机交付和继续产品化都比较友好

## 本地运行

安装前端依赖：

```powershell
pnpm install
```

启动前后端开发模式：

```powershell
pnpm dev
```

前端默认地址：

```text
http://127.0.0.1:8790
```

后端默认地址：

```text
http://127.0.0.1:8791
```

启动桌面壳：

```powershell
pnpm desktop
```

## 验证记录

本次归档前已完成以下最小验证：

- `pnpm build` 通过
- `pnpm validate` 通过
  - TypeScript 无输出校验通过
  - Python `compileall` 通过

## 归档说明

本仓库保留的是对继续开发和交付有价值的正式源码内容，不包含以下无必要中间产物：

- `node_modules/`
- `dist/`
- 运行期生成的 `runtime/projects/*` 实际项目数据
- 本地日志与缓存

运行目录结构仍被保留，便于后续继续开发或恢复运行环境。

---

## English Overview

Video Text Translator is a Windows desktop application project for replacing burned-in foreign text in videos with translated overlay text and exporting a new MP4 file.

The system is organized as a three-part local architecture:

- Electron for the desktop shell
- React for the operator interface
- FastAPI plus Python processing modules for video inspection, storage, OCR adapters, translation adapters, and export jobs

### Main capabilities

- create projects from local files or browser upload
- inspect source videos and extract preview frames
- define text replacement regions visually
- persist project state locally
- render translated overlays into a new MP4 output
- preserve the original source file
- keep and remux audio when present
- extend OCR and translation providers through adapter-based integration

### Recommended workflow

```powershell
pnpm install
pnpm dev
pnpm build
pnpm validate
```

This repository is suitable for continued private development, desktop delivery, and later product hardening around OCR integration, translation provider switching, export control, and packaging.
