#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path('/home/ubuntu/.openclaw/workspace')
BOT = ROOT / 'projects' / 'bullpen-bot'
DASH = ROOT / 'projects' / 'bullpen-dashboard'
STATE = BOT / 'state'
REPORTS = BOT / 'reports'
OUT = DASH / 'dashboard-data.json'


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def parse_key_value_report(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    ledger = load_json(STATE / 'paper_ledger.json', {'cash': 0, 'open_positions': [], 'closed_positions': []})
    mtm = load_json(STATE / 'paper_mark_to_market.json', {'positions': []})
    convergence = load_json(STATE / 'convergence_snapshot.json', {'signals': []})
    daily_metrics = load_json(STATE / 'paper_daily_metrics.json', {})
    events = []
    events_path = STATE / 'paper_events.jsonl'
    if events_path.exists():
        for line in events_path.read_text().splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))

    daily_summary = parse_key_value_report(REPORTS / 'paper_daily_summary.txt')
    rolling_summary = parse_key_value_report(REPORTS / 'paper_rolling_summary.txt')
    trader_summary = parse_key_value_report(REPORTS / 'paper_trader_summary.txt')
    exit_summary = parse_key_value_report(REPORTS / 'paper_exit_summary.txt')

    latest_day = max(daily_metrics) if daily_metrics else None
    latest_metrics = daily_metrics.get(latest_day, {}) if latest_day else {}

    open_trade_ids = {p.get('trade_id') for p in ledger.get('open_positions', [])}
    mtm_index = {p.get('trade_id'): p for p in mtm.get('positions', [])}
    open_positions = []
    for pos in ledger.get('open_positions', []):
        mark = mtm_index.get(pos.get('trade_id'), {})
        open_positions.append({
            'title': pos.get('title'),
            'side': pos.get('side'),
            'entry_price': pos.get('entry_price'),
            'entry_usd': pos.get('entry_usd'),
            'wallet_count': pos.get('wallet_count'),
            'buying_wallets': pos.get('buying_wallets'),
            'avg_wallet_score': pos.get('avg_wallet_score'),
            'opened_at': pos.get('opened_at'),
            'current_price': mark.get('current_price'),
            'unrealized_pnl': mark.get('unrealized_pnl', 0),
            'return_pct': mark.get('return_pct', 0),
        })

    closed_positions = []
    for pos in ledger.get('closed_positions', [])[-20:][::-1]:
        closed_positions.append({
            'title': pos.get('title'),
            'side': pos.get('side'),
            'entry_price': pos.get('entry_price'),
            'exit_price': pos.get('exit_price'),
            'realized_pnl': pos.get('realized_pnl'),
            'exit_reason': pos.get('exit_reason'),
            'opened_at': pos.get('opened_at'),
            'closed_at': pos.get('closed_at'),
        })

    signals = []
    for sig in convergence.get('signals', [])[:12]:
        signals.append({
            'title': sig.get('title'),
            'side': sig.get('side'),
            'wallet_count': sig.get('wallet_count'),
            'buying_wallets': sig.get('buying_wallets'),
            'selling_wallets': sig.get('selling_wallets'),
            'avg_wallet_score': sig.get('avg_wallet_score'),
            'momentum_score': sig.get('momentum_score'),
            'price': sig.get('price'),
            'consecutive_count': sig.get('consecutive_count'),
        })

    recent_activity = []
    for ev in events[-20:][::-1]:
        recent_activity.append({
            'timestamp': ev.get('timestamp'),
            'type': ev.get('type'),
            'title': ev.get('title'),
            'reason': ev.get('reason') or ev.get('exit_reason'),
            'realized_pnl': ev.get('realized_pnl'),
        })

    equity_curve = []
    for ev in events:
        if ev.get('type') == 'run_snapshot':
            equity_curve.append({
                'timestamp': ev.get('timestamp'),
                'ending_equity': ev.get('ending_equity'),
                'cash': ev.get('cash'),
            })

    data = {
        'title': 'Lavbot Bullpen Dashboard',
        'updated_at': convergence.get('timestamp') or ledger.get('timestamp'),
        'summary': {
            'cash': ledger.get('cash', 0),
            'open_positions': len(ledger.get('open_positions', [])),
            'closed_positions': len(ledger.get('closed_positions', [])),
            'realized_pnl': latest_metrics.get('realized_pnl', 0),
            'win_rate': latest_metrics.get('win_rate', 0),
            'ending_equity': float(daily_summary.get('ending_equity', ledger.get('cash', 0)) or 0),
            'total_return': float(rolling_summary.get('total_return', 0) or 0),
            'signals_now': convergence.get('signal_count', 0),
        },
        'daily': latest_metrics,
        'rolling': rolling_summary,
        'open_positions': open_positions,
        'closed_positions': closed_positions,
        'signals': signals,
        'recent_activity': recent_activity,
        'equity_curve': equity_curve,
        'meta': {
            'daily_summary': daily_summary,
            'trader_summary': trader_summary,
            'exit_summary': exit_summary,
        }
    }

    DASH.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'path': str(OUT), 'signals': len(signals), 'open_positions': len(open_positions), 'closed_positions': len(closed_positions)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
