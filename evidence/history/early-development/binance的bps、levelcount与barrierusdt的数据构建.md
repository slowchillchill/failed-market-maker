我们以这个数据样本source://v2/model/1774334400-1774420500为例，构建binance的btcusdt在5min周期中的bps与levelCount与barrierUsdt的指标。

1、构建binance的btcusdt在5min周期中的bps与levelCount与barrierUsdt的指标，作为强化学习的特征。bps是基于binance的btcusdt的毫秒级aggtrades价格数据计算的:每个5分钟市场开始时刻的binance btcusdt价格是price to beat，实时的binance btcusdt价格是current price，5分钟结束时的binance btcusdt价格是resolution price。levelCount与barrierUsdt是基于binance的btcusdt的毫秒级orderbook订单簿数据计算的。
2、注意这里的5分钟市场的开始时间和结束时间应当与polymarket的btc-updown-5m-orderbook订单簿数据的时间对齐。
3、数据应当保存在对应的数据集目录下的bps-levelcount-barrierusdt/文件夹中，如：model/20260326/1774411200-1774425600/bps-levelcount-barrierusdt/
4、文件名命名应与polymarket的btc-updown-5m的文件名称对齐，格式为{时间戳范围}-btcusdt-blb.ndjson，如：1774411200-1774425600-btcusdt-blb.ndjson
5、文件内容格式是"{timestamp_ms}:{bps}:{levelCount}:{barrierUsdt}"，如：1774411200000:+100.00:+100.00:+100000.00;统一保留小数点后两位；+表示正数，-表示负数。正数表达current price大于price to beat，负数表达current price小于price to beat。
6、构建脚本为model/build_blb_features.py，示例命令：

```bash
# --sample-ms 1 表示每毫秒采样一次（毫秒级精度）
python3 model/build_blb_features.py --model-root model/20260325/1774248000-1774334100 --sample-ms 1
```
