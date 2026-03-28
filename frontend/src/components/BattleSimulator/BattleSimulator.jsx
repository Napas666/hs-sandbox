import React from 'react';
import { useStore } from '../../store/useStore';
import './BattleSimulator.css';

function WinBar({ winA, tie, winB }) {
  return (
    <div className="win-bar">
      <div className="win-bar__segment win-bar__a" style={{ width: `${winA}%` }}>
        {winA > 8 && <span>{winA}%</span>}
      </div>
      <div className="win-bar__segment win-bar__tie" style={{ width: `${tie}%` }}>
        {tie > 6 && <span>{tie}%</span>}
      </div>
      <div className="win-bar__segment win-bar__b" style={{ width: `${winB}%` }}>
        {winB > 8 && <span>{winB}%</span>}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  return (
    <div className="result-stat-card" style={{ '--stat-color': color }}>
      <div className="result-stat-card__icon">{icon}</div>
      <div className="result-stat-card__val">{value}</div>
      <div className="result-stat-card__lbl">{label}</div>
    </div>
  );
}

export default function BattleSimulator() {
  const { playerBoard, enemyBoard, simResult, simLoading, simError, simulate, clearSimResult } = useStore();

  const canSimulate = playerBoard.length > 0 && enemyBoard.length > 0;

  const getVerdict = () => {
    if (!simResult) return null;
    if (simResult.verdict === 'YOUR_BOARD') return { text: '🏆 Your Board Wins!', cls: 'verdict--win' };
    if (simResult.verdict === 'ENEMY_BOARD') return { text: '💀 Enemy Wins', cls: 'verdict--loss' };
    return { text: '⚖️ It\'s a Toss-Up', cls: 'verdict--tie' };
  };

  const verdict = getVerdict();

  return (
    <div className="battle-simulator">
      <div className="sim-header">
        <h2 className="sim-title">⚔️ Battle Simulator</h2>
        <p className="sim-subtitle">Simulate 1,000 battles to find win probability</p>
      </div>

      {/* Board preview */}
      <div className="sim-boards-preview">
        <div className="sim-board-preview sim-board-preview--player">
          <div className="sbp-label">Your Board</div>
          <div className="sbp-count">{playerBoard.length} minion{playerBoard.length !== 1 ? 's' : ''}</div>
          <div className="sbp-names">
            {playerBoard.map(m => <span key={m.instanceId} className="sbp-name">{m.name}</span>)}
            {playerBoard.length === 0 && <span className="sbp-empty">No minions</span>}
          </div>
          <div className="sbp-stats">
            <span>⚔ {playerBoard.reduce((s,m) => s+(m.currentAttack??m.attack),0)}</span>
            <span>♥ {playerBoard.reduce((s,m) => s+(m.currentHealth??m.health),0)}</span>
          </div>
        </div>

        <div className="sim-vs">VS</div>

        <div className="sim-board-preview sim-board-preview--enemy">
          <div className="sbp-label">Enemy Board</div>
          <div className="sbp-count">{enemyBoard.length} minion{enemyBoard.length !== 1 ? 's' : ''}</div>
          <div className="sbp-names">
            {enemyBoard.map(m => <span key={m.instanceId} className="sbp-name">{m.name}</span>)}
            {enemyBoard.length === 0 && <span className="sbp-empty">No minions</span>}
          </div>
          <div className="sbp-stats">
            <span>⚔ {enemyBoard.reduce((s,m) => s+(m.currentAttack??m.attack),0)}</span>
            <span>♥ {enemyBoard.reduce((s,m) => s+(m.currentHealth??m.health),0)}</span>
          </div>
        </div>
      </div>

      {/* Simulate button */}
      <button
        className={`sim-btn ${canSimulate ? 'sim-btn--ready' : 'sim-btn--disabled'} ${simLoading ? 'sim-btn--loading' : ''}`}
        onClick={canSimulate ? simulate : undefined}
        disabled={!canSimulate || simLoading}
      >
        {simLoading ? (
          <><div className="btn-spinner" /> Simulating 1,000 battles...</>
        ) : (
          <>⚔️ Simulate Battle</>
        )}
      </button>

      {!canSimulate && (
        <p className="sim-warning">Add minions to both boards first</p>
      )}

      {simError && <div className="sim-error">⚠️ {simError}</div>}

      {/* Results */}
      {simResult && (
        <div className="sim-results animate-fade-in">
          <div className={`sim-verdict ${verdict?.cls}`}>{verdict?.text}</div>

          <WinBar
            winA={simResult.win_rate_a}
            tie={simResult.tie_rate}
            winB={simResult.win_rate_b}
          />

          <div className="win-bar-labels">
            <span className="wbl-a">You {simResult.win_rate_a}%</span>
            {simResult.tie_rate > 0 && <span className="wbl-tie">Tie {simResult.tie_rate}%</span>}
            <span className="wbl-b">Enemy {simResult.win_rate_b}%</span>
          </div>

          <div className="result-stats-grid">
            <StatCard icon="⚔" label="Your Win Rate" value={`${simResult.win_rate_a}%`} color="#60a5fa" />
            <StatCard icon="⚖️" label="Tie Rate" value={`${simResult.tie_rate}%`} color="#a78bfa" />
            <StatCard icon="💀" label="Enemy Win Rate" value={`${simResult.win_rate_b}%`} color="#f87171" />
            <StatCard icon="♥" label="Avg HP Left (You)" value={simResult.avg_remaining_health_a.toFixed(1)} color="#2ecc71" />
            <StatCard icon="💔" label="Avg HP Left (Enemy)" value={simResult.avg_remaining_health_b.toFixed(1)} color="#e67e22" />
            <StatCard icon="🎲" label="Simulations" value={simResult.iterations.toLocaleString()} color="#f4d03f" />
          </div>

          <button className="clear-results-btn" onClick={clearSimResult}>Clear Results</button>
        </div>
      )}
    </div>
  );
}
