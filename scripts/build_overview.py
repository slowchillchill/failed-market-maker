"""Regenerate README score tables, card summaries and figures from published records.

Run with Python 3 from any directory. No model loading, network calls or hashes.
Narrative text stays in Markdown; numeric tables come from catalog/, with IQL
window returns read from the existing source-cited RESULTS.md table.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = {p.stem: json.loads(p.read_text()) for p in (ROOT / 'catalog').glob('*.json')}
MODELS = [v for v in DATA.values() if isinstance(v, dict) and 'model_id' in v]
MODELS.sort(key=lambda m: (list(['m3', 'm5_bc', 'm5_iql', 'alpha_v2', 'maker_policy_v2', 'maker_policy_v2_repair', 'deployment']).index(m['family']), m['model_id']))
PAPER = DATA['paper-results']
LIVE = sorted(DATA['live-results'], key=lambda x: x['run_id'])
RUNS = sorted({x['run_id'] for x in PAPER}, key=lambda s: s[-16:])
PROFILES = ['m3_b1', 'm3_b2', 'm5_baseline', 'mpv2_r1_a3_seq120_seed2']
IQL = {}
for i in range(3):
    match = re.search(r'\| IQL-' + str(i) + r' \| ([+−.0-9]+)% \| ([+−.0-9]+)% \|', (ROOT / 'RESULTS.md').read_text())
    IQL[f'm5_iql_{i}'] = [float(x.replace('−', '-')) for x in match.groups()]


def alias(mid):
    names = {'m3_run3': 'M3 run3', 'm3_run_v7_M3-B1': 'M3 B1', 'm3_run_v7_M3-B2': 'M3 B2', 'm5_v7v72_bc': 'M5 BC', 'policy_phase67_C0_control_anchor': '6.7 C0', 'policy_phase67_P1_signed_reward_filter': '6.7 P1', 'mpv2_r1_a3_seq120_seed2': 'R1 Alpha + Policy'}
    if mid in names:
        return names[mid]
    if mid.startswith('m5_iql_'):
        return 'IQL-' + mid[-1]
    m = re.search(r'(R\d)_(A\d|LB2|C2).*seed(\d)', mid)
    return f'{m[1]} {m[2]} · s{m[3]}'


def number(value, digits=6, signed=False):
    return format(float(value), ('+' if signed else '') + f',.{digits}f')


def table(headers, rows):
    return '\n'.join('| ' + ' | '.join(map(str, row)) + ' |' for row in [headers, ['---'] * len(headers), *rows])


def replace_block(text, name, content):
    pattern = rf'<!-- {name}:start -->.*?<!-- {name}:end -->'
    result, count = re.subn(pattern, lambda _: f'<!-- {name}:start -->\n{content}\n<!-- {name}:end -->', text, flags=re.S)
    assert count == 1, name
    return result


def candidate_row(m):
    z, family = m['metrics'], m['family']
    name = f'[{alias(m["model_id"])}](models/{m["model_id"]}/README.md)'
    if family == 'm3':
        return 'm3', [name, z['best_epoch'], number(z['train_loss']), number(z['val_auc']), number(z['test']['auc']), number(z['test']['top_decile_mean_ev_up'], signed=True)]
    if family == 'm5_bc':
        return 'bc', [name, z['best_epoch'], *[number(z['best_checkpoint_accuracy'][x]) for x in ['train', 'val', 'test']]]
    if family == 'm5_iql':
        return 'iql', [name, z['best_epoch'], number(z['best_policy_loss']), number(z['best_val_q_loss']), f'{z["best_hold_share"]*100:.2f}% / {z["final_hold_share"]*100:.2f}%', *[number(x, 4, True) + '%' for x in IQL[m['model_id']]]]
    if family == 'alpha_v2':
        return 'alpha', [name, z['best_epoch'], *[number(z[x]) for x in ['train_loss', 'val.auc', 'true_best_side_auc']], number(z['selected_side_top_decile_ev'], signed=True)]
    records = [x for x in DATA['offline-results'] if x['model_id'] == m['model_id']]
    a = next(x for x in records if x['phase'] in ['phase65', 'phase67'])
    independent = next((x for x in records if x['phase'] == 'phase66'), None)
    return 'policy', [name, '6.7' if family.endswith('repair') else '6.5', number(z['last_bc_loss'], 9), number(z['last_offline_rl_loss'], 9), number(a['pnl_usdc'], 2, True), number(independent['pnl_usdc'], 2, True) if independent else None]


def svg_start(width, height, title, bg='#ffffff'):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title, quote=True)}">', f'<title>{html.escape(title)}</title>', f'<rect width="{width}" height="{height}" rx="12" fill="{bg}"/>']


def svg_text(x, y, text, size=16, color='#263e39', anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,Noto Sans CJK SC,sans-serif" font-size="{size}" text-anchor="{anchor}">{html.escape(str(text))}</text>'


def write_svg(name, pieces):
    (ROOT / 'figures' / name).write_text('\n'.join(pieces + ['</svg>']) + '\n')


def figures(lang, T):
    counts = (sum(m['training_candidate'] for m in MODELS), len(RUNS), len(LIVE))
    title = T('24 models. Promising simulations. No established live edge.', '24 个模型。曾经亮眼的模拟成绩。未被证实的实盘优势。')
    p = svg_start(1000, 270, title, '#142b33')
    p += [svg_text(36, 37, 'POLYMARKET  /  BTC UP & DOWN  /  5 MIN', 13, '#a6cebd'), svg_text(36, 98, 'The Failed Market Maker.', 44, '#f5f5ef'), svg_text(36, 142, T('From predictive signals to the limits of live execution.', '从预测信号，到实盘执行的边界。'), 21, '#cbded6')]
    for x, n, label in zip([36, 358, 682], counts, [T('retained models', '个留存训练候选'), T('paper runs', '次模拟盘运行'), T('live reports', '份可归属实盘报告')]):
        p += [svg_text(x, 222, n, 40, '#8dd8b7'), svg_text(x + 70, 216, label, 18, '#d9e9e1')]
    write_svg(f'overview-{lang}.svg', p)
    p = svg_start(1000, 330, T('June 2 paper run: adjusted PnL, USDC', '6 月 2 日模拟盘：调整后收益，USDC'))
    p += [svg_text(28, 35, T('ONE PAPER RUN · FOUR PROFILES', '同一轮模拟盘 · 四个组合'), 19), svg_text(28, 62, T('2026-06-02 run · decisions stopped June 5 · adjusted PnL / USDC', '2026-06-02 运行 · 6 月 5 日停止决策 · 调整后收益 / USDC'), 14, '#566e64')]
    zero, scale = 350, 0.29
    p.append(f'<line x1="{zero}" x2="{zero}" y1="83" y2="270" stroke="#a4b7ad"/>')
    for i, (profile, label) in enumerate(zip(PROFILES, ['M3 B1', 'M3 B2', 'M5 BC', 'R1 Alpha + Policy'])):
        value = next(x['pnl_usdc'] for x in PAPER if x['run_id'] == RUNS[-1] and x['profile_id'] == profile)
        y, width = 94 + i * 45, abs(value) * scale
        color = '#167658' if value >= 0 else '#b64132'
        x = zero if value >= 0 else zero - width
        p += [svg_text(28, y + 22, label), f'<rect x="{x:.2f}" y="{y}" width="{width:.2f}" height="30" fill="{color}" rx="3"/>', svg_text(zero + width + 10 if value >= 0 else zero - width - 10, y + 22, number(value, 2, True), 16, color, 'start' if value >= 0 else 'end')]
    p += [svg_text(28, 305, T('Simulation only. Not a completed seven-day test. Values are not live account returns.', '仅为模拟成绩；未完成七天测试，不代表实盘账户收益。'), 14, '#566e64')]
    write_svg(f'paper-latest-{lang}.svg', p)
    p = svg_start(1000, 310, T('IQL: fixed versus native execution', 'IQL：固定执行与原生执行'))
    p += [svg_text(28, 35, T('IQL · SAME CANDIDATE, DIFFERENT EXECUTION', 'IQL · 同一候选，不同执行方式'), 19), svg_text(28, 64, T('Mean return across 24 offline validation windows (%) · not paper or live', '24 个离线验证窗口的平均收益率（%）· 非模拟盘或实盘'), 14, '#566e64')]
    p += [svg_text(660, 94, T('Fixed', '固定执行'), 14, '#176d91'), svg_text(810, 94, T('Native', '原生执行'), 14, '#a74731')]
    for i, (mid, values) in enumerate(IQL.items()):
        y = 109 + i * 62
        p.append(svg_text(28, y + 24, alias(mid)))
        for j, v in enumerate(values):
            width, zero, yy = abs(v) * 78, 360, y + j * 23
            color = ['#176d91', '#a74731'][j]
            p += [f'<rect x="{zero if v >= 0 else zero-width:.2f}" y="{yy}" width="{width:.2f}" height="17" fill="{color}"/>', svg_text(zero + width + 8 if v >= 0 else zero - width - 8, yy + 14, number(v, 4, True) + '%', 14, color, 'start' if v >= 0 else 'end')]
    p.append('<line x1="360" x2="360" y1="102" y2="283" stroke="#8da396"/>')
    write_svg(f'iql-execution-{lang}.svg', p)


def build(lang):
    zh = lang == 'zh'
    T = lambda en, cn: cn if zh else en
    path = ROOT / ('README.zh-CN.md' if zh else 'README.md')
    text = path.read_text()
    latest = next(x for x in PAPER if x['run_id'] == RUNS[-1] and x['profile_id'] == PROFILES[-1])
    summary = table([T('Paper · R1 deployment', '模拟盘 · R1 部署组合'), T('Live · latest attributable report', '实盘 · 最新可归属报告'), T('Final platform account PnL', '平台最终账户收益')], [[f'**{number(latest["pnl_usdc"], 2, True)} USDC**', f'**{number(LIVE[-1]["pnl"]["model_local_conservative_nav_delta"], 4, True)} USDC**', '**N/A**'], [T('June 2 run · adjusted PnL', '6 月 2 日运行 · 调整后收益'), T('June 22 12:06 UTC · local conservative NAV change', '6 月 22 日 12:06 UTC · 本地保守 NAV 变化'), T('All 13 reports unreconciled', '13 份报告均未核对')], [T('Decisions stopped June 5; not seven full days', '6 月 5 日停止决策；未完成七天'), T('Includes unrealized inventory', '包含未实现持仓'), T('No verified cumulative account return', '无经核对的累计账户收益')]])
    text = replace_block(text, 'summary', summary)
    rows = {key: [] for key in ['m3', 'bc', 'iql', 'alpha', 'policy']}
    headers = {}
    for name in rows:
        block = re.search(rf'<!-- {name}:start -->\n(.*?)\n<!-- {name}:end -->', text, re.S)[1]
        headers[name] = [x.strip() for x in block.splitlines()[0].strip('|').split('|')]
    card_rows = {}
    for m in MODELS:
        if not m['training_candidate']:
            continue
        family, row = candidate_row(m)
        row = [T('N/A · not independently tested', 'N/A · 未独立测试') if x is None else x for x in row]
        rows[family].append(row)
        card_rows[m['model_id']] = (headers[family], row)
    for key in rows:
        text = replace_block(text, key, table(headers[key], rows[key]))
    rows_missing = []
    for a in DATA['alpha-experiments']:
        if a['weights'] != 'retained':
            z = a['val']
            rows_missing.append([alias(a['run_id']), number(z['auc']), number(z['true_best_side_auc']), number(z['selected_side_top_decile_ev'], signed=True), T('N/A · not retained', 'N/A · 未留存')])
    text = replace_block(text, 'alpha-missing', table([T('Experiment', '实验'), 'val.auc', 'true_best_side_auc', T('Val selected-side top-decile EV', '验证选定方向最高十分位 EV'), T('Weights', '权重')], rows_missing))
    dates = ['05.17 · 02:21', '05.17 · 22:34', '05.19 → 05.22', '05.27 → 05.30', '06.02 → 06.05']
    durations = [T('6.22 h · stopped early', '6.22 小时 · 提前停止'), T('39.30 h · stopped early', '39.30 小时 · 提前停止'), T('72.07 h', '72.07 小时'), T('71.98 h', '71.98 小时'), T('Decisions stopped June 5', '6 月 5 日停止决策')]
    paper_rows = []
    for i, run in enumerate(RUNS):
        source = next(x['source'] for x in PAPER if x['run_id'] == run)
        row = [f'[{dates[i]}]({source})<br>{durations[i]}', T('NAV change', 'NAV 变化') if i == 0 else T('Adjusted PnL', '调整后收益')]
        for profile in PROFILES:
            x = next((x for x in PAPER if x['run_id'] == run and x['profile_id'] == profile), None)
            row.append(number(x['pnl_usdc'], 2, True) if x else T('N/A · not included', 'N/A · 未包含'))
        paper_rows.append(row)
    text = replace_block(text, 'paper-table', table([T('Run / duration', '运行／时长'), T('Metric', '口径'), 'M3 B1', 'M3 B2', 'M5 BC', 'R1 Alpha + Policy'], paper_rows))
    live_rows = []
    for x in LIVE:
        run, p = x['run_id'][-16:], x['pnl']
        stamp = f'{run[4:6]}.{run[6:8]} {run[9:11]}:{run[11:13]}:{run[13:15]}'
        live_rows.append([f'[{stamp}]({x["source"]})', number(p['model_local_conservative_nav_delta'], signed=True) if p['nav_observable'] else T('N/A · unobservable', 'N/A · 不可观测'), number(p['model_local_realized_pnl'], signed=True), T('N/A · not reconciled', 'N/A · 未核对')])
    text = replace_block(text, 'live-table', table([T('UTC run', 'UTC 运行时间'), T('Local NAV change', '本地 NAV 变化'), T('Realized only', '仅已实现部分'), T('Final platform PnL', '平台最终收益')], live_rows))
    path.write_text(text)
    figures(lang, T)
    return card_rows


def cards(en, zh):
    for m in MODELS:
        path = ROOT / 'models' / m['model_id'] / 'README.md'
        text = path.read_text()
        if m['training_candidate']:
            he, re_ = en[m['model_id']]
            hz, rz = zh[m['model_id']]
            summary = table(['Metric / 指标', 'Result / 成绩'], [[f'{he[i]} / {hz[i]}', str(re_[i]) if re_[i] == rz[i] else f'{re_[i]} / {rz[i]}'] for i in range(1, len(he))])
            family = m['family']
            if family.startswith('maker_policy'):
                summary += '\n\n**' + ('FAIL_CONTROL_AMPLIFICATION' if family.endswith('repair') else 'FAIL_NO_MAKER_EDGE') + '**. Replay sums are independent-window USDC, not account returns. Independent val/test loss: N/A — no report. / 回放为独立窗口收益之和，单位 USDC，不是账户收益。独立验证／测试损失 N/A：无报告。\n'
            if family == 'm5_iql':
                summary += '\n\nReturns: mean of 24 offline validation windows. ONNX = best checkpoint; final = epoch 50. / 收益率为 24 个离线验证窗口均值；ONNX 来自最佳权重，末轮为第 50 轮。\n'
            if family == 'alpha_v2':
                summary += '\n\nIndependent test N/A — not executed. / 独立测试 N/A：未执行。\n'
            profile = {'m3_run_v7_M3-B1': 'm3_b1', 'm3_run_v7_M3-B2': 'm3_b2', 'm5_v7v72_bc': 'm5_baseline'}.get(m['model_id'])
            if profile:
                summary += '\n\n**Paper / 模拟盘 — all five runs / 全部五轮（USDC）**\n\n' + table(['UTC run / 运行', 'Metric / 口径', 'PnL'], [[f'[{x["run_id"][-16:]}](../../{x["source"]})', x['metric'], number(x['pnl_usdc'], 4, True)] for x in sorted(PAPER, key=lambda x: x['run_id'][-16:]) if x['profile_id'] == profile])
                summary += '\n\nSignal outputs plus external execution/risk rules; June 2 run stopped early. Live N/A — no corresponding evidence. / 使用 signal 输出和外部执行风控；6 月 2 日运行提前结束。实盘 N/A：无对应证据。'
            else:
                summary += '\n\nStandalone paper/live **N/A — no corresponding standalone reports**. / 单体模拟盘与实盘 **N/A：无对应独立报告**。'
        else:
            summary = '**Deployment combination, not a 25th trained candidate. / 部署组合，不是第 25 个训练候选。**\n\n'
            summary += table(['Paper run (UTC) / 模拟盘运行', 'Adjusted PnL / 调整后收益（USDC）'], [[f'[{x["run_id"][-16:]}](../../{x["source"]})', number(x['pnl_usdc'], 4, True)] for x in sorted(PAPER, key=lambda x: x['run_id'][-16:]) if x['profile_id'] == PROFILES[-1]])
            summary += '\n\nJune 2 run: decisions stopped June 5, not a completed seven-day test. / 6 月 2 日运行于 6 月 5 日停止决策，未完成七天测试。\n\n'
            summary += f'**Live / 实盘:** {len(LIVE)} reports; {sum(x["pnl"]["nav_observable"] for x in LIVE)} observable local NAV deltas. Platform final PnL **N/A — not reconciled in all 13 reports**. / 13 份报告中 6 份可观测本地 NAV 变化，平台最终收益 **N/A：全部尚未核对**。'
        summary += '\n\n[All results and limitations / 全部成绩与限制](../../RESULTS.md) · [完整中文](../../RESULTS.zh-CN.md)\n'
        if '<!-- scorecard:start -->' not in text:
            split = text.index('\n\n')
            text = text[:split] + '\n\n<!-- scorecard:start -->\n<!-- scorecard:end -->' + text[split:]
        path.write_text(replace_block(text, 'scorecard', summary))


def main():
    cards(build('en'), build('zh'))
    print('Updated two READMEs, 25 card summaries and six figures from published records.')


if __name__ == '__main__':
    main()
