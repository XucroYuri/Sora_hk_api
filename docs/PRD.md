# 项目需求文档 (PRD): Sora 视频批量生成工具

## 1. 项目概述

本项目旨在开发一个高效的后端脚本程序，通过调用 Sora API，根据预设的分镜脚本批量生成视频。程序支持多线程并发处理，能够扫描统一的 `input` 目录读取 JSON 格式的分镜数据，并将生成的视频及其相关素材规范、可靠地保存到 `output` 目录中。

## 2. 核心功能

### 2.1 输入处理 (Input Processing)
- **输入源灵活配置**:
  - 默认扫描目录: `./input`。
  - 支持自定义输入目录: 通过命令行参数 `--input-dir <path>` 指定。
- **递归扫描 (Recursive Discovery)**:
  - 遍历指定目录及其**所有子目录**。
  - **过滤条件**: 
    1. 文件名包含特定前缀 `storyboard` (不区分大小写)。
    2. 文件扩展名为 `.json`。
    3. 内容结构校验通过（必须包含符合 schema 的 `segments` 数组）。
- **任务组构建**:
  - 每个符合条件的 JSON 文件视为一个**任务组 (Task Group)**。
  - 总任务数 = (JSON 文件数) * (Segment 数) * (每 Segment 重复生成数)。

### 2.2 视频生成与参数配置
- **API 集成**: 对接 `https://api.sora.hk/v1` 接口。
- **参数优先级 (Parameter Override)**:
  采用 **Segment 级 > 环境变量/全局配置 > 默认值** 的级联策略。
- **标准模板**: 在 `input/` 目录下提供 `_template.json` 示例文件。
- **状态轮询**: 智能轮询 `GET /tasks/:task_id`。

### 2.3 流程控制与并发
- **优雅退出 (Graceful Shutdown)**:
  - 捕获 `SIGINT` (Ctrl+C)。
  - 停止分发新任务，等待进行中的写入操作原子化完成后退出，并清理残留的临时文件。
- **网络代理**:
  - 默认支持系统代理配置（如本地 10808 端口）。
  - 可在 `.env` 中通过 `HTTP_PROXY` 显式覆盖。
- **断点续传 (Skip Existing)**: 
  - 检查机制: 生成前检查目标文件是否存在。
- **空跑模式 (Dry Run)**: 估算成本与任务量。
- **交互式 UI**: 使用 `rich` 展示进度。
- **失败重试**: 失败队列与重试机制。

### 2.4 输出管理 (Output Strategy)
- **输出模式选择**: 支持两种回写策略 (通过 `--output-mode` 参数控制)：
  1. **集中式 (Centralized - Default)**: 统一写入到 `./output` 目录，保持原有层级结构。
     ```
     output/{Source_SubDir_Structure}/{Json_Filename}/{Segment}/...
     ```
  2. **原位回写 (In-Place)**: 直接写回到 JSON 文件所在的同级目录下。
     ```
     {Source_Dir}/{Json_Filename}_assets/{Segment}/...
     ```
- **文件命名**: `{SegmentIndex}_v{Version}_{ShortTaskID}.mp4`。
- **可靠保存**: 流式下载 + 原子写入 (tmp -> mp4)。

### 2.4 异常处理与重试
- **智能重试**: 对网络错误（Connection Error）或 5xx 错误进行指数退避重试（最多 3-5 次）。
- **失败队列 (Dead Letter Queue)**:
  - 所有最终失败的任务记录到 `output/failed_tasks_{timestamp}.json`。
  - 支持 `--retry-failed <json_file>` 模式，仅读取该文件重新尝试失败的任务，无需全量扫描。

### 2.5 输出管理 (可靠性与规范)
- **配置文件**: 在根目录下支持 `.env` 文件或 `config.yaml`（优先使用 `.env`）。
- **参数项**:
  - `SORA_API_KEY`: 用户填入的真实 API Key。
  - `SORA_BASE_URL`: API 基础路径（默认 `https://api.sora.hk/v1`）。
  - `MAX_CONCURRENT_TASKS`: 全局最大并发任务数。
  - `GEN_COUNT_PER_SEGMENT`: 每个 Segment 生成的数量（默认 2）。

## 3. 技术方案

### 3.1 技术栈
- **语言**: Python 3.9+
- **核心库**: `requests` (HTTP), `concurrent.futures` (并发), `pathlib` (路径处理), `logging` (日志), `python-dotenv` (配置管理)

### 3.2 模块设计
... (保持原有设计)

## 4. 开发计划
... (保持原有计划)

## 5. 用户确认项
1. **输入位置**: 确认使用根目录下的 `input/` 文件夹作为唯一输入源。
2. **输入格式**: 确认输入文件为标准 JSON 格式。
3. **输出规范**: 确认按 `{Filename}/{Segment}/...` 结构归档。
4. **生成数量**: 确认每个 Segment 默认生成 2 个视频。
5. **配置方式**: 确认通过 `.env` 文件管理 API Key。

---
**下一步**: 待用户确认本 PRD 后，开始进行目录初始化和代码编写。