import React, { useState } from 'react';
import { useStore } from '../../store/useStore';
import { SPELLS } from '../../utils/spells';
import './SpellPanel.css';

export default function SpellPanel() {
  const { playerBoard, enemyBoard, selectedBoardTarget, updateMinionWithSpell } = useStore();
  const [selectedSpell, setSelectedSpell] = useState(null);
  const board = selectedBoardTarget === 'player' ? playerBoard : enemyBoard;

  const handleCastOnMinion = (minion) => {
    if (!selectedSpell) return;
    updateMinionWithSpell(minion.instanceId, selectedBoardTarget, selectedSpell);
    if (!selectedSpell.boardWide) setSelectedSpell(null);
  };

  const handleCastAll = () => {
    if (!selectedSpell || !selectedSpell.boardWide) return;
    board.forEach(m => updateMinionWithSpell(m.instanceId, selectedBoardTarget, selectedSpell));
    setSelectedSpell(null);
  };

  return (
    <div className="spell-panel">
      <div className="spell-panel__header">
        <h3 className="spell-title">🪄 Tavern Spells</h3>
        <div className="spell-target-hint">
          Casting on: <span className={`spell-target ${selectedBoardTarget}`}>
            {selectedBoardTarget === 'player' ? '⚔ Your Board' : '💀 Enemy Board'}
          </span>
        </div>
      </div>

      {/* Spell grid */}
      <div className="spell-grid">
        {SPELLS.map(spell => (
          <button
            key={spell.id}
            className={`spell-btn ${selectedSpell?.id === spell.id ? 'spell-btn--active' : ''}`}
            style={{ '--spell-color': spell.color }}
            onClick={() => setSelectedSpell(selectedSpell?.id === spell.id ? null : spell)}
            title={spell.desc}
          >
            <span className="spell-icon">{spell.icon}</span>
            <span className="spell-name">{spell.name}</span>
          </button>
        ))}
      </div>

      {/* Selected spell info */}
      {selectedSpell && (
        <div className="spell-selected" style={{ '--spell-color': selectedSpell.color }}>
          <div className="spell-selected__icon">{selectedSpell.icon}</div>
          <div className="spell-selected__info">
            <div className="spell-selected__name">{selectedSpell.name}</div>
            <div className="spell-selected__desc">{selectedSpell.desc}</div>
          </div>
          {selectedSpell.boardWide
            ? <button className="spell-cast-all-btn" onClick={handleCastAll}>Cast All</button>
            : <div className="spell-click-hint">↓ Click a minion below to cast</div>
          }
        </div>
      )}

      {/* Minion targets */}
      {selectedSpell && !selectedSpell.boardWide && (
        <div className="spell-targets">
          {board.length === 0
            ? <div className="spell-no-targets">No minions on board</div>
            : board.map(m => (
                <button
                  key={m.instanceId}
                  className="spell-target-minion"
                  onClick={() => handleCastOnMinion(m)}
                >
                  <span className="stm-icon">{selectedSpell.icon}</span>
                  <span className="stm-name">{m.name}</span>
                  <span className="stm-stats">
                    ⚔{m.currentAttack ?? m.attack} ♥{m.currentHealth ?? m.health}
                  </span>
                </button>
              ))
          }
        </div>
      )}
    </div>
  );
}
