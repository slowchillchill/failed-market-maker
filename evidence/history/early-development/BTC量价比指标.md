# BTC量价指标（简化版）

## 1. 指标目标

该指标只回答一个问题：`CP` 到 `P2B` 之间的盘口屏障是否足够强。

- 如果这段区间里的挂单总额（按 `USDT` 计）足够厚，并且价格层级足够大，输出 `green`
- 只要挂单不够厚，或者价格层级不够大，输出 `red`

本指标适用于 `Polymarket` 的 `BTC UP DOWN 5min` 连续市场。

## 2. 核心定义

- `CP`：当前参考价格
- `P2B`：当前关键判定价格
- `levelCount`：`CP` 与 `P2B` 之间的价格层级数，步长固定为 `0.01 USDT`
- `barrierUsdt`：`CP` 与 `P2B` 之间同方向盘口挂单的累计金额，单位为 `USDT`

## 3. 统计方向

### 3.1 当 `CP < P2B`

说明价格若继续上涨，会向上穿过 `P2B`。

- 统计 `ask` 侧从 `CP` 上方到 `P2B` 之间的挂单
- 把这些挂单按 `price * qty` 累加，得到 `barrierUsdt`

### 3.2 当 `CP > P2B`

说明价格若继续下跌，会向下穿过 `P2B`。

- 统计 `bid` 侧从 `CP` 下方到 `P2B` 之间的挂单
- 把这些挂单按 `price * qty` 累加，得到 `barrierUsdt`

### 3.3 当 `CP = P2B`

- 直接输出 `red`

## 4. 计算方式

### 4.1 价格层级数

`levelCount = ceil(abs(P2B - CP) / 0.01)`

### 4.2 挂单总额

`barrierUsdt = sum(price_i * qty_i)`

说明：

- 只统计 `CP` 到 `P2B` 之间、会阻挡价格穿越 `P2B` 的那一侧挂单
- 不再看平均每层挂单、`bps`、`lotDensity` 等衍生指标

## 5. 信号判定

### 5.1 绿灯

同时满足以下两个条件时，输出 `green`：

- `barrierUsdt >= barrierUsdtThreshold`
- `levelCount >= levelCountThreshold`

含义：

- 挂单金额够厚，说明流动性屏障强
- 价格层级够大，说明 `CP` 到 `P2B` 之间还有足够距离

### 5.2 红灯

满足以下任一条件时，输出 `red`：

- `barrierUsdt < barrierUsdtThreshold`
- `levelCount < levelCountThreshold`
- `CP = P2B`
- 盘口数据缺失、过期或方向无法判断

## 6. 阈值配置

阈值不写死在文档里，交给程序配置：

- `barrierUsdtThreshold`：最小挂单总额要求
- `levelCountThreshold`：最小价格层级要求

后续通过回测和实盘观察不断调整这两个阈值即可。

## 7. 输出字段

建议输出：

- `signal`：`green` 或 `red`
- `canOpenPosition`
- `allowStopLoss`
- `allowInsurance`
- `levelCount`
- `barrierUsdt`
- `direction`：`up_cross` 或 `down_cross`
- `reasonCode`

建议的 `reasonCode`：

- `GREEN_BARRIER_STRONG`
- `RED_BARRIER_THIN`
- `RED_LEVEL_TOO_SMALL`
- `RED_AT_P2B`
- `RED_INVALID_DATA`

## 8. 与交易程序的联动

### 8.1 当 `signal = green`

- 允许新增建仓

### 8.2 当 `signal = red`

- 禁止新增建仓
- 只允许止损与保险单交易

## 9. 异常处理

以下情况一律输出 `red`：

- `CP` 或 `P2B` 缺失
- orderbook 快照超时
- `CP` 到 `P2B` 之间没有可用盘口数据
- 盘口档位明显缺失

## 10. 示例

### 10.1 输出绿灯

- `CP = 108000.00`
- `P2B = 108003.20`
- `levelCount = 320`
- `barrierUsdt = 145000`
- `barrierUsdtThreshold = 100000`
- `levelCountThreshold = 300`

判定：

- 挂单金额够厚
- 价格层级够大
- 输出 `green`

### 10.2 输出红灯

- `CP = 108000.00`
- `P2B = 107999.20`
- `levelCount = 80`
- `barrierUsdt = 18000`
- `barrierUsdtThreshold = 100000`
- `levelCountThreshold = 300`

判定：

- 挂单金额不够厚
- 价格层级也不够大
- 输出 `red`