# Sora HK 视频批量生成工具 (Sora Batch Generator)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个企业级的 Sora 视频批量生成后端程序，专为高并发、大规模任务设计。支持断点续传、自适应并发控制、自动重试与素材整理。

## ✨ 核心特性

*   **⚡️ 高效并发**: 基于 `ThreadPoolExecutor` 的多线程架构，默认支持 20 线程并发。
*   **🛡️ 自适应熔断 (Circuit Breaker)**: 
    *   **智能降级**: 当检测到连续 API 错误（如 429/5xx）时，自动将并发数从 20 降级为 5（安全模式）。
    *   **缓慢恢复**: 触发熔断后冷却 10 分钟，随后每分钟自动释放 1 个并发名额，直至恢复满载。
*   **💾 断点续传**: 生成前自动检查输出目录，已存在且完整的文件会自动跳过 (Skipped)，避免重复扣费。
*   **🎥 长时任务支持**: 针对 Pro 模型优化的轮询策略，支持最长 35 分钟的生成等待，内置 Request ID 追踪。
*   **🔄 健壮性设计**:
    *   **防惊群 (Jitter)**: 任务启动随机抖动，防止瞬间流量冲击。
    *   **原子写入**: 文件先下载为 `.tmp`，校验完整后重命名，杜绝损坏文件。
    *   **内存保护**: 流式下载 (1MB Chunk) + 主动 GC 回收。
*   **🖥️ 全中文交互**: 漂亮的 CLI 界面，支持 Ctrl+C 优雅退出。

## 🛠️ 快速开始

### 1. 环境准备

确保已安装 Python 3.9 或更高版本。

```bash
# 1. 克隆项目
git clone https://github.com/XucroYuri/Sora_hk_api.git
cd Sora_hk_api

# 2. 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

复制配置模板并填入你的 Key：

```bash
cp .env.example .env
# 编辑 .env 文件，填入 SORA_API_KEY=sk-xxxx
```

> **安全提示**: 请勿将包含真实 Key 的 `.env` 文件提交到代码仓库。本项目已配置 `.gitignore` 进行保护。

### 3. 准备分镜脚本

在 `input/` 目录下创建 JSON 文件（必须以 `storyboard` 开头，如 `storyboard_01.json`）。模板参考 `input/_template.json`。

```json
{
  "segments": [
    {
      "segment_index": 1,
      "prompt_text": "一只在雨中漫步的赛博朋克猫咪",
      "duration_seconds": 10,
      "is_pro": false,
      "resolution": "horizontal"
    }
  ]
}
```

### 4. 运行程序

**macOS / Linux:**
```bash
./start_mac.sh
```

**Windows:**
双击 `start_win.bat`

---

## ⚙️ 高级用法

### 空跑模式 (Dry Run)
在不消耗 API 额度的情况下，预演任务队列并估算成本。
```bash
python main.py --dry-run
```

### 自定义输入输出
```bash
# 指定输入目录，并将结果原位保存在输入文件旁边
python main.py --input-dir "/Users/Me/Obsidian/Projects" --output-mode in_place
```

### 参数说明

| 参数 | 说明 |
| :--- | :--- |
| `--input-dir` | 自定义分镜 JSON 所在的目录（支持递归扫描） |
| `--output-mode` | `centralized` (默认，存到 output/) 或 `in_place` (存到 JSON 同级) |
| `--force` | 强制覆盖已生成的视频文件 |
| `--verbose` | 显示详细的调试日志 (Debug 模式) |

---

## 🔒 安全与限制

*   **API Key 保护**: 日志系统会自动脱敏 API Key (`sk-******`)，确保日志文件安全。
*   **并发限制**: 默认最大并发 20。若触发 API 速率限制，系统会自动进入“安全模式”，请勿强行终止，等待其自动恢复即可。
*   **磁盘保护**: 下载时会自动检测磁盘空间，若空间不足 (`ENOSPC`) 会自动停止写入并报警。

## 📂 目录结构

```
.
├── input/                  # 默认输入目录
│   ├── _template.json      # 分镜模板
│   └── storyboard_demo.json
├── output/                 # 默认输出目录
├── src/                    # 源代码
│   ├── api_client.py       # API 交互与连接池
│   ├── concurrency.py      # 自适应并发控制器
│   ├── downloader.py       # 流式下载
│   └── worker.py           # 任务逻辑
├── main.py                 # 程序入口
└── .env                    # 配置文件 (需自行创建)
```

## 📝 License

MIT License
