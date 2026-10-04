# GPU 服务器部署方案

> 目标：将完整开发环境迁移到云端 GPU 服务器，完成 M5 S4-S5（全量 tick_stream 采集 + IQL 训练 + 评估）。

---

## 1. 服务器规格

| 项目 | 规格 |
|------|------|
| GPU | NVIDIA RTX 5090 (32GB VRAM) |
| CPU | 25 vCPU Intel Xeon 8470Q |
| RAM | 90GB |
| 系统 | PyTorch 2.8.0, Python 3.12, CUDA 12.8 |
| 系统盘 | 30GB |
| 数据盘 | **需扩展至 500GB**（见磁盘规划） |
| 登录 | `ssh -p 39557 root@[REDACTED_TRAINING_HOST]` |

---

## 2. 磁盘空间规划

### 当前数据体量

| 数据类别 | 大小 | 说明 |
|----------|------|------|
| 原始数据 data-v1 | ~56 GB | model/data-v1/ |
| 原始数据 data-v2 | ~92 GB | model/data-v2/ |
| 原始数据 data-v3 | ~169 GB | model/data-v3/ |
| M0 管线产出 | ~18 GB | data-pipeline/out/ |
| feature-engine 产出 | ~314 MB | feature-engine/out/ |
| M3 checkpoint | ~5.4 MB | checkpoints/m3_run3/ |
| **原始数据合计** | **~335 GB** | |

### 预期新增

| 数据类别 | 预计大小 | 说明 |
|----------|----------|------|
| tick_stream parquet (3 datasets) | ~2-3 GB | S4-B 全量采集产出 |
| M5 训练产出 | ~100 MB | checkpoints + ONNX + stats |
| Rust 编译缓存 | ~7 GB | target/ |
| Python 依赖 | ~3 GB | .venv/ |
| 系统 + 工具链 | ~5 GB | Rust toolchain 等 |
| **新增合计** | **~18 GB** | |

### 磁盘总需求

```
原始数据:      ~335 GB
M0 产出:       ~18 GB
新增产出:      ~18 GB
冗余余量:      ~30 GB（编译/临时文件/日志）
─────────────────────
总计:          ~400 GB
建议数据盘:    500 GB（留足空间应对 data-v3 增量和多轮实验）
```

---

## 3. 目录结构（服务器端）

```
[PRIVATE_ROOT]/
├── poly-arb-2/                    # 完整仓库（含代码 + 数据）
│   ├── model/
│   │   ├── data-v1/               # 原始数据（~56GB）
│   │   ├── data-v2/               # 原始数据（~92GB）
│   │   └── data-v3/               # 原始数据（~169GB）
│   ├── poly-arb-ai/
│   │   ├── data-pipeline/out/     # M0 产出（~18GB）
│   │   ├── rust/                  # Rust workspace
│   │   │   └── feature-engine/out/  # 特征帧产出
│   │   └── training/
│   │       └── checkpoints/m3_run3/  # M3 backbone
│   └── tick_stream/               # M5 tick_stream 产出（~2-3GB）
├── m5_run1/                       # M5 训练产出目录
└── .venv/                         # Python 虚拟环境
```

**建议**：整个仓库（含 model/ 数据目录）统一放在数据盘挂载点下，避免系统盘空间不足。若数据盘挂载在 `[PRIVATE_ROOT]/` 以外路径（如 `/data/`），可用符号链接 `ln -s /data/poly-arb-2 [PRIVATE_ROOT]/poly-arb-2`。

---

## 4. 环境部署步骤

### 4.1 数据盘扩展与挂载

```bash
# 1. 在 SeetaCloud 控制台扩展数据盘至 500GB
# 2. SSH 登录后确认挂载点
df -h
lsblk

# 3. 若数据盘未自动挂载，手动格式化并挂载
# mkfs.ext4 /dev/vdb  # 仅首次！谨慎操作
# mount /dev/vdb [PRIVATE_ROOT]/data
# echo '/dev/vdb [PRIVATE_ROOT]/data ext4 defaults 0 0' >> /etc/fstab
```

### 4.2 系统工具安装

```bash
# 基础工具（部分可能已预装）
apt-get update && apt-get install -y \
    build-essential cmake pkg-config \
    git curl wget rsync \
    libssl-dev

# Rust 工具链
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustup default stable
# 验证
rustc --version  # 需 >= 1.75（ort 2.0.0-rc.12 要求）
```

### 4.3 Python 环境

```bash
# 服务器预装 PyTorch 2.8.0+cu128 + Python 3.12
# 确认 CUDA 可用
python3 -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"

# 创建虚拟环境（复用系统 PyTorch）
python3 -m venv [PRIVATE_ROOT]/.venv --system-site-packages
source [PRIVATE_ROOT]/.venv/bin/activate

# 安装项目依赖
pip install numpy pyarrow scipy scikit-learn tqdm onnx onnxruntime
# 验证
python3 -c "import torch, pyarrow, numpy; print('OK')"
```

### 4.4 数据传输

**方案 A：rsync 增量同步（推荐）**

从本地机器执行，按优先级分批传输：

```bash
# 批次 1：代码 + M3 checkpoint + M0 产出 + feature-engine 产出（~20GB，最优先）
rsync -avz --progress \
    --exclude='model/data-*' \
    --exclude='poly-arb-ai/rust/target' \
    --exclude='.venv' \
    --exclude='tick_stream' \
    --exclude='__pycache__' \
    -e 'ssh -p 39557' \
    source://v2/ \
    root@[REDACTED_TRAINING_HOST]:[PRIVATE_ROOT]/poly-arb-2/

# 批次 2：原始数据 data-v1（~56GB）
rsync -avz --progress \
    -e 'ssh -p 39557' \
    source://v2/model/data-v1/ \
    root@[REDACTED_TRAINING_HOST]:[PRIVATE_ROOT]/poly-arb-2/model/data-v1/

# 批次 3：原始数据 data-v2（~92GB）
rsync -avz --progress \
    -e 'ssh -p 39557' \
    source://v2/model/data-v2/ \
    root@[REDACTED_TRAINING_HOST]:[PRIVATE_ROOT]/poly-arb-2/model/data-v2/

# 批次 4：原始数据 data-v3（~169GB）
rsync -avz --progress \
    -e 'ssh -p 39557' \
    source://v2/model/data-v3/ \
    root@[REDACTED_TRAINING_HOST]:[PRIVATE_ROOT]/poly-arb-2/model/data-v3/
```

预计传输时间取决于上行带宽：
- 100 Mbps 上行：~335GB ≈ 7-8 小时
- 30 Mbps 上行：~335GB ≈ 24+ 小时

**方案 B：仅传输必要数据（快速启动）**

如果带宽受限，可先只传代码 + M0/M2 产出，省略原始数据。但 **collect-transitions 需要原始数据**（replay-engine 从原始 ndjson/csv 读取），所以最终仍需全量传输。

折中方案：先传 data-v1（最小，56GB）跑通全流程验证，再并行传 v2/v3。

```bash
# 先传代码 + 产出 + data-v1
rsync -avz --progress \
    --exclude='model/data-v2' \
    --exclude='model/data-v3' \
    --exclude='poly-arb-ai/rust/target' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    -e 'ssh -p 39557' \
    source://v2/ \
    root@[REDACTED_TRAINING_HOST]:[PRIVATE_ROOT]/poly-arb-2/
```

### 4.5 Rust 编译验证

```bash
cd [PRIVATE_ROOT]/poly-arb-2

# 编译全 workspace
cargo build --release --manifest-path poly-arb-ai/rust/Cargo.toml --workspace

# 运行全部测试
cargo test --manifest-path poly-arb-ai/rust/Cargo.toml --workspace
# 预期：76 passed
```

### 4.6 Python 测试验证

```bash
cd [PRIVATE_ROOT]/poly-arb-2
source [PRIVATE_ROOT]/.venv/bin/activate

# M5 IQL 测试
PYTHONPATH=poly-arb-ai python3 -m pytest poly-arb-ai/training/test_iql.py -v
# 预期：19 passed

# M3 模型测试
PYTHONPATH=poly-arb-ai python3 -m pytest poly-arb-ai/training/test_model.py -v

# 全部 training 测试
PYTHONPATH=poly-arb-ai python3 -m pytest poly-arb-ai/training/ -v
# 预期：67 passed
```

---

## 5. M5 S4-S5 执行计划

### 5.1 S4-A：ONNX 重导出（collection 模式）

```bash
cd [PRIVATE_ROOT]/poly-arb-2
source [PRIVATE_ROOT]/.venv/bin/activate

PYTHONPATH=poly-arb-ai python3 poly-arb-ai/training/export_onnx.py \
    --mode collection \
    --backbone-checkpoint poly-arb-ai/training/checkpoints/m3_run3/best_model.pt \
    --backbone-stats poly-arb-ai/training/checkpoints/m3_run3/feature_stats.npz \
    --seq-len 240 \
    --output [PRIVATE_ROOT]/poly-arb-2/agent_model_76_collection.onnx
```

### 5.2 S4-B：全量 tick_stream 采集（CPU 密集，25 vCPU）

```bash
# 创建输出目录
mkdir -p [PRIVATE_ROOT]/poly-arb-2/tick_stream

# data-v1（预计 ~20-30 分钟）
cargo run --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- \
    collect-transitions \
    --model-path [PRIVATE_ROOT]/poly-arb-2/agent_model_76_collection.onnx \
    --dataset-version data-v1 \
    --output [PRIVATE_ROOT]/poly-arb-2/tick_stream/v1.parquet \
    2>&1 | tee [PRIVATE_ROOT]/poly-arb-2/tick_stream/v1.log

# data-v2
cargo run --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- \
    collect-transitions \
    --model-path [PRIVATE_ROOT]/poly-arb-2/agent_model_76_collection.onnx \
    --dataset-version data-v2 \
    --output [PRIVATE_ROOT]/poly-arb-2/tick_stream/v2.parquet \
    2>&1 | tee [PRIVATE_ROOT]/poly-arb-2/tick_stream/v2.log

# data-v3
cargo run --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- \
    collect-transitions \
    --model-path [PRIVATE_ROOT]/poly-arb-2/agent_model_76_collection.onnx \
    --dataset-version data-v3 \
    --output [PRIVATE_ROOT]/poly-arb-2/tick_stream/v3.parquet \
    2>&1 | tee [PRIVATE_ROOT]/poly-arb-2/tick_stream/v3.log
```

### 5.3 S4-C：Reward 理智检查

```bash
# 历史对照命令；当前默认请使用 reward_minimal 口径
PYTHONPATH=poly-arb-ai python3 poly-arb-ai/training/validate_transitions.py \
    --tick-stream-paths tick_stream/v1_reward_minimal.parquet tick_stream/v2_reward_minimal.parquet tick_stream/v3_reward_minimal.parquet
```

### 5.4 S4-D：IQL 训练（GPU）

```bash
PYTHONPATH=poly-arb-ai python3 -u poly-arb-ai/training/train_iql.py \
    --tick-stream-paths \
        [PRIVATE_ROOT]/poly-arb-2/tick_stream/v1_reward_minimal.parquet \
        [PRIVATE_ROOT]/poly-arb-2/tick_stream/v2_reward_minimal.parquet \
        [PRIVATE_ROOT]/poly-arb-2/tick_stream/v3_reward_minimal.parquet \
    --backbone-checkpoint poly-arb-ai/training/checkpoints/m3_run3/best_model.pt \
    --backbone-stats poly-arb-ai/training/checkpoints/m3_run3/feature_stats.npz \
    --epochs 50 --batch-size 2048 \
    --gamma 0.9995 --tau 0.7 --beta 3.0 \
    --lr-policy 1e-4 --lr-q 3e-4 --lr-v 3e-4 \
    --output-dir [PRIVATE_ROOT]/m5_run1 \
    --device cuda --num-workers 8 \
    2>&1 | tee [PRIVATE_ROOT]/m5_run1.log
```

RTX 5090 (32GB VRAM) + batch=2048 预计 VRAM 占用 < 10GB，可进一步增大 batch_size 至 4096 或 8192 以提高 GPU 利用率。

### 5.5 S5：评估（需先实现 evaluate 子命令）

```bash
# M5 trained agent 评估
cargo run --release --manifest-path poly-arb-ai/rust/Cargo.toml -p agent -- \
    evaluate \
    --model-path [PRIVATE_ROOT]/m5_run1/agent_model_m5.onnx \
    --split-info [PRIVATE_ROOT]/m5_run1/split_info.json \
    --split test \
    --override-risk-score 1.0

# 基线对比（需先实现 baseline_strategies.rs）
# Hold-only 基线
cargo run --release ... -- evaluate --strategy hold --split-info ... --split test

# Signal-heuristic 基线
cargo run --release ... -- evaluate --strategy signal-heuristic --split-info ... --split test
```

---

## 6. 产出回传

训练完成后，将关键产出同步回本地：

```bash
# 从本地执行
rsync -avz --progress \
    -e 'ssh -p 39557' \
    root@[REDACTED_TRAINING_HOST]:[PRIVATE_ROOT]/m5_run1/ \
    source://v2/poly-arb-ai/training/checkpoints/m5_run1/

# tick_stream（如需本地留存）
rsync -avz --progress \
    -e 'ssh -p 39557' \
    root@[REDACTED_TRAINING_HOST]:[PRIVATE_ROOT]/poly-arb-2/tick_stream/ \
    source://v2/tick_stream/
```

---

## 7. 注意事项

1. **数据盘挂载**：确保 `[PRIVATE_ROOT]/poly-arb-2/model/` 在数据盘上，系统盘 30GB 放不下原始数据
2. **Python 版本**：服务器 Python 3.12 vs 本地可能不同，torch 版本也不同（2.8.0 vs 2.4.1），但代码无版本特定 API
3. **Rust 编译**：首次编译 ~5-10 分钟（包含 ort 下载 ONNX Runtime 预编译库），后续增量编译 < 30 秒
4. **ort ONNX Runtime**：ort 2.0.0-rc.12 会自动下载 ONNX Runtime 动态库；若服务器无外网，需手动放置 `libonnxruntime.so` 或设置 `ORT_LIB_LOCATION`
5. **rsync 断点续传**：rsync 天然支持断点续传，网络中断后重新执行相同命令即可
6. **nohup / tmux**：长时间任务（采集/训练）建议在 tmux 中运行，避免 SSH 断连丢失进度
7. **M3 训练经验**：RTX 5090 + batch=2048 + AMP 时 GPU 利用率 ~92%，M5 IQL 训练结构类似，预计表现相当
