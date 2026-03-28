import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useStore } from '../../store/useStore';
import { RACE_COLORS, TIER_COLORS } from '../../utils/constants';
import './BattleArena.css';

const API = '/api';
const STEP_MS = 800; // ms between events

function ArenaMinion({ minion, isAttacking, isTargeted, isDsPopped, isDead, isNew, side }) {
  const tierColor = TIER_COLORS[minion.tier] || '#9ca3af';
  const raceColor = RACE_COLORS[minion.race]  || '#374151';
  const [imgErr, setImgErr] = useState(false);

  const classes = [
    'arena-minion',
    `arena-minion--${side}`,
    isAttacking ? 'arena-minion--attacking' : '',
    isTargeted  ? 'arena-minion--targeted'  : '',
    isDsPopped  ? 'arena-minion--ds-pop'    : '',
    isDead      ? 'arena-minion--dead'      : '',
    isNew       ? 'arena-minion--new'       : '',
    minion.divine_shield ? 'arena-minion--ds' : '',
    minion.taunt ? 'arena-minion--taunt' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} style={{ '--tier': tierColor, '--race': raceColor }}>
      {minion.taunt && <div className="arena-taunt-ring" />}
      {minion.divine_shield && <div className="arena-ds-ring" />}

      <div className="arena-minion__art">
        {minion.image_url && !imgErr
          ? <img src={minion.image_url} alt={minion.name} onError={() => setImgErr(true)} />
          : <div className="arena-art-fallback" style={{ background: `radial-gradient(circle at 40% 35%, ${raceColor} 0%, #0a0608 100%)` }}>
              {minion.name?.charAt(0)}
            </div>
        }
        {isDead && <div className="arena-death-x">✕</div>}
      </div>

      <div className="arena-minion__name">{minion.name}</div>
      <div className="arena-minion__stats">
        <span className="s-atk">⚔{minion.attack}</span>
        <span className="s-hp" style={{ color: minion.health <= 0 ? '#ef4444' : '#34d399' }}>
          ♥{minion.health}
        </span>
      </div>

      {/* keyword icons */}
      <div className="arena-keywords">
        {minion.divine_shield && <span title="Divine Shield">🛡️</span>}
        {minion.taunt         && <span title="Taunt">🗡️</span>}
        {minion.windfury      && <span title="Windfury">💨</span>}
        {minion.poisonous     && <span title="Poisonous">☠️</span>}
        {minion.reborn        && <span title="Reborn">🔄</span>}
        {minion.cleave        && <span title="Cleave">⚔️</span>}
      </div>
    </div>
  );
}

function EventLog({ events, currentIdx }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [currentIdx]);

  const shown = events.slice(0, currentIdx + 1).filter(e => e.type !== 'start');
  return (
    <div className="event-log" ref={ref}>
      {shown.map((ev, i) => {
        let text = '';
        let icon = '';
        switch (ev.type) {
          case 'attack':       icon='⚔️'; text=`${ev.attacker_side} attacks → ${ev.target_side}`; break;
          case 'death':        icon='💀'; text=`${ev.name} dies`; break;
          case 'spawn':        icon='✨'; text=`${ev.name} spawned (${ev.attack}/${ev.health})`; break;
          case 'reborn':       icon='🔄'; text=`${ev.name} reborn`; break;
          case 'divine_shield_pop': icon='💥'; text=`Divine Shield popped`; break;
          case 'end':          icon='🏆'; text=`Winner: ${ev.winner} (${ev.remaining_hp} HP left)`; break;
          default: return null;
        }
        return (
          <div key={i} className={`log-entry log-entry--${ev.type}`}>
            <span className="log-icon">{icon}</span>
            <span className="log-text">{text}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function BattleArena({ onClose }) {
  const { playerBoard, enemyBoard } = useStore();
  const [events, setEvents]       = useState([]);
  const [currentIdx, setCurrentIdx] = useState(-1);
  const [playing, setPlaying]     = useState(false);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [speed, setSpeed]         = useState(800);
  const timerRef = useRef(null);

  // current board state from event
  const currentBoards = events[currentIdx]?.boards || events[0]?.boards || null;
  const activeEvent   = events[currentIdx] || null;

  const fetchReplay = useCallback(async () => {
    setLoading(true); setError(null); setEvents([]); setCurrentIdx(-1);
    try {
      const toMinion = m => ({
        id: m.id, name: m.name,
        attack: m.currentAttack ?? m.attack,
        health: m.currentHealth ?? m.health,
        mechanics: m.mechanics || [],
        divine_shield: m.divine_shield || false,
        taunt: m.taunt || false,
        cleave: m.cleave || false,
        poisonous: m.poisonous || false,
        windfury: m.windfury || false,
        reborn: m.reborn || false,
      });
      const res = await axios.post(`${API}/simulate/replay`, {
        board_a: playerBoard.map(toMinion),
        board_b: enemyBoard.map(toMinion),
      });
      // Enrich board snapshots with image_url from our store
      const enrichedEvents = res.data.events.map(ev => {
        if (!ev.boards) return ev;
        const enrich = (minions, storeBoard) => minions.map(m => {
          const src = storeBoard.find(s => s.id === m.id);
          return { ...m, image_url: src?.image_url || null, race: src?.race || 'Neutral', tier: src?.tier || 1 };
        });
        return {
          ...ev,
          boards: {
            A: enrich(ev.boards.A, playerBoard),
            B: enrich(ev.boards.B, enemyBoard),
          }
        };
      });
      setEvents(enrichedEvents);
      setCurrentIdx(0);
    } catch(e) {
      setError('Failed to load battle replay');
    }
    setLoading(false);
  }, [playerBoard, enemyBoard]);

  useEffect(() => { fetchReplay(); }, []);

  // Autoplay
  useEffect(() => {
    if (!playing) { clearInterval(timerRef.current); return; }
    timerRef.current = setInterval(() => {
      setCurrentIdx(i => {
        if (i >= events.length - 1) { setPlaying(false); return i; }
        return i + 1;
      });
    }, speed);
    return () => clearInterval(timerRef.current);
  }, [playing, events.length, speed]);

  const step = (dir) => {
    setPlaying(false);
    setCurrentIdx(i => Math.min(Math.max(0, i + dir), events.length - 1));
  };

  const atk_uid   = activeEvent?.type === 'attack' ? activeEvent.attacker_uid : null;
  const tgt_uid   = activeEvent?.type === 'attack' ? activeEvent.target_uid   : null;
  const ds_uid    = activeEvent?.type === 'divine_shield_pop' ? activeEvent.uid : null;
  const dead_uids = events.slice(0, currentIdx + 1)
    .filter(e => e.type === 'death')
    .map(e => e.uid);
  const new_uids  = activeEvent?.type === 'spawn' ? [activeEvent.uid] :
                    activeEvent?.type === 'reborn' ? [activeEvent.uid] : [];

  const winner = events[events.length - 1]?.winner;
  const isEnd  = currentIdx === events.length - 1;

  return (
    <div className="battle-arena-overlay" onClick={onClose}>
      <div className="battle-arena" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="arena-header">
          <div className="arena-title">⚔️ Battle Replay</div>
          <div className="arena-controls">
            <button className="arena-btn" onClick={() => { setPlaying(false); setCurrentIdx(0); }}>⏮</button>
            <button className="arena-btn" onClick={() => step(-1)}>◀</button>
            <button className="arena-btn arena-btn--play" onClick={() => setPlaying(p => !p)}>
              {playing ? '⏸' : '▶'}
            </button>
            <button className="arena-btn" onClick={() => step(1)}>▶</button>
            <button className="arena-btn" onClick={() => { setPlaying(false); setCurrentIdx(events.length - 1); }}>⏭</button>
            <select className="speed-select" value={speed} onChange={e => setSpeed(Number(e.target.value))}>
              <option value={1200}>0.5×</option>
              <option value={800}>1×</option>
              <option value={400}>2×</option>
              <option value={150}>4×</option>
            </select>
          </div>
          <button className="arena-close" onClick={onClose}>✕</button>
        </div>

        {/* Progress */}
        <div className="arena-progress">
          <div className="arena-progress__bar"
            style={{ width: events.length ? `${(currentIdx/(events.length-1))*100}%` : '0%' }} />
        </div>

        {loading && <div className="arena-loading"><div className="arena-spinner"/><span>Simulating battle…</span></div>}
        {error   && <div className="arena-error">{error}</div>}

        {/* Battlefield */}
        {currentBoards && (
          <div className="arena-battlefield">
            {/* Your board */}
            <div className="arena-side arena-side--player">
              <div className="arena-side__label">⚔ Your Board</div>
              <div className="arena-minions">
                {currentBoards.A.map(m => (
                  <ArenaMinion key={m.uid} minion={m} side="A"
                    isAttacking={m.uid === atk_uid}
                    isTargeted={m.uid === tgt_uid}
                    isDsPopped={m.uid === ds_uid}
                    isDead={dead_uids.includes(m.uid) && !m.alive}
                    isNew={new_uids.includes(m.uid)} />
                ))}
              </div>
            </div>

            <div className="arena-vs-divider">
              {isEnd
                ? <div className={`arena-winner-badge ${winner === 'A' ? 'w-a' : winner === 'B' ? 'w-b' : 'w-tie'}`}>
                    {winner === 'A' ? '🏆 You Win!' : winner === 'B' ? '💀 Enemy Wins' : '⚖️ Tie'}
                  </div>
                : <div className="arena-vs-text">VS</div>
              }
            </div>

            {/* Enemy board */}
            <div className="arena-side arena-side--enemy">
              <div className="arena-side__label">💀 Enemy Board</div>
              <div className="arena-minions">
                {currentBoards.B.map(m => (
                  <ArenaMinion key={m.uid} minion={m} side="B"
                    isAttacking={m.uid === atk_uid}
                    isTargeted={m.uid === tgt_uid}
                    isDsPopped={m.uid === ds_uid}
                    isDead={dead_uids.includes(m.uid) && !m.alive}
                    isNew={new_uids.includes(m.uid)} />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Event log */}
        {events.length > 0 && (
          <EventLog events={events} currentIdx={currentIdx} />
        )}

        {/* Reload */}
        <div className="arena-footer">
          <button className="arena-reload-btn" onClick={fetchReplay}>🎲 New Battle</button>
          <span className="arena-step-counter">
            {events.length > 0 ? `Step ${currentIdx+1} / ${events.length}` : ''}
          </span>
        </div>
      </div>
    </div>
  );
}
