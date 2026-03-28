import React, { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import MinionCard from '../UI/MinionCard';
import { RACES, MECHANICS, MECHANIC_LABELS, TIER_COLORS } from '../../utils/constants';
import './CardLibrary.css';

export default function CardLibrary() {
  const {
    cards, cardsLoading, cardsError,
    filters, fetchCards, setFilter,
    addToBoard, selectedBoardTarget,
    playerBoard, enemyBoard,
  } = useStore();
  const [search, setSearch] = useState('');

  useEffect(() => { fetchCards(); }, []);

  const currentBoard = selectedBoardTarget === 'player' ? playerBoard : enemyBoard;

  // Count how many of each card are already on the active board
  const copyCounts = currentBoard.reduce((acc, m) => {
    acc[m.id] = (acc[m.id] || 0) + (m.isGold ? 3 : 1);
    return acc;
  }, {});

  const filtered = cards.filter(c =>
    !search || c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="card-library">
      <div className="library-header">
        <h2 className="library-title">📚 Card Library</h2>
        <div className="adding-to">
          Adding to: <span className={`adding-target ${selectedBoardTarget}`}>
            {selectedBoardTarget === 'player' ? '⚔ Your Board' : '💀 Enemy Board'}
          </span>
        </div>
      </div>

      <div className="library-search">
        <input className="search-input" placeholder="Search cards..." value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      <div className="library-filters">
        <div className="filter-group">
          <label className="filter-label">Tier</label>
          <div className="filter-chips">
            <button className={`filter-chip ${!filters.tier ? 'active' : ''}`} onClick={() => setFilter('tier', null)}>All</button>
            {[1,2,3,4,5,6,7].map(t => (
              <button key={t}
                className={`filter-chip ${filters.tier === t ? 'active' : ''}`}
                style={{ '--chip-color': TIER_COLORS[t] }}
                onClick={() => setFilter('tier', filters.tier === t ? null : t)}
              >⭐{t}</button>
            ))}
          </div>
        </div>
        <div className="filter-group">
          <label className="filter-label">Race</label>
          <div className="filter-chips">
            <button className={`filter-chip ${!filters.race ? 'active' : ''}`} onClick={() => setFilter('race', '')}>All</button>
            {RACES.filter(r => r !== 'Neutral').map(r => (
              <button key={r}
                className={`filter-chip ${filters.race === r ? 'active' : ''}`}
                onClick={() => setFilter('race', filters.race === r ? '' : r)}
              >{r}</button>
            ))}
          </div>
        </div>
        <div className="filter-group">
          <label className="filter-label">Keyword</label>
          <div className="filter-chips">
            <button className={`filter-chip ${!filters.mechanic ? 'active' : ''}`} onClick={() => setFilter('mechanic', '')}>All</button>
            {MECHANICS.map(m => (
              <button key={m}
                className={`filter-chip ${filters.mechanic === m ? 'active' : ''}`}
                onClick={() => setFilter('mechanic', filters.mechanic === m ? '' : m)}
              >{MECHANIC_LABELS[m]}</button>
            ))}
          </div>
        </div>
      </div>

      <div className="library-count">{filtered.length} cards</div>

      <div className="library-grid">
        {cardsLoading && (
          <div className="library-loading">
            <div className="loading-spinner" />
            <span>Loading cards...</span>
          </div>
        )}
        {cardsError && <div className="library-error">⚠️ {cardsError}</div>}
        {!cardsLoading && filtered.map(card => {
          const copies = copyCounts[card.id] || 0;
          return (
            <div key={card.id} className="library-card-wrap">
              <MinionCard
                minion={card}
                size="sm"
                onAdd={c => addToBoard(c, selectedBoardTarget)}
              />
              {/* Copy counter dots */}
              {copies > 0 && (
                <div className="copy-dots">
                  {[1,2,3].map(i => (
                    <span key={i} className={`copy-dot ${i <= copies ? 'copy-dot--filled' : ''} ${copies >= 3 ? 'copy-dot--gold' : ''}`} />
                  ))}
                </div>
              )}
              {copies >= 3 && <div className="copy-gold-label">✨ GOLD</div>}
            </div>
          );
        })}
        {!cardsLoading && !cardsError && filtered.length === 0 && (
          <div className="library-empty">No cards found</div>
        )}
      </div>
    </div>
  );
}
