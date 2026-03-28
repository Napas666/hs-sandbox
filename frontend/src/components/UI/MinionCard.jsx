import React, { useState } from 'react';
import { MECHANIC_ICONS, MECHANIC_LABELS, RACE_COLORS, TIER_COLORS } from '../../utils/constants';
import './MinionCard.css';

const RACE_EMOJI = {
  Beast:'🐾', Demon:'👿', Dragon:'🐉', Elemental:'🌊',
  Mech:'⚙️', Murloc:'🐟', Pirate:'☠️', Quilboar:'🐗',
  Undead:'💀', Neutral:'⚔️', Naga:'🐍',
};

// BG-tier frame colors — like the stars on the card
const TIER_FRAME = {
  1: { bg:'#2a2035', border:'#7a6a8a', star:'#a090b0', glow:'rgba(160,144,176,0.3)' },
  2: { bg:'#1a2a1a', border:'#5a8a5a', star:'#70b070', glow:'rgba(96,160,96,0.3)' },
  3: { bg:'#1a2240', border:'#4a6aaa', star:'#6a9aff', glow:'rgba(96,144,240,0.35)' },
  4: { bg:'#2a1a40', border:'#8a5ab0', star:'#c080ff', glow:'rgba(176,96,240,0.35)' },
  5: { bg:'#2a1e0a', border:'#b07020', star:'#ffc040', glow:'rgba(255,192,64,0.4)' },
  6: { bg:'#2a0a0a', border:'#aa4040', star:'#ff8060', glow:'rgba(255,96,64,0.4)' },
  7: { bg:'#1a1a0a', border:'#b0a010', star:'#ffe040', glow:'rgba(255,224,0,0.5)' },
};

function TierStars({ tier }) {
  const frame = TIER_FRAME[tier] || TIER_FRAME[1];
  const count = Math.min(tier, 6);
  return (
    <div className="bg-card__stars">
      {Array.from({ length: count }).map((_, i) => (
        <span key={i} className="bg-card__star" style={{ color: frame.star }}>★</span>
      ))}
      {tier === 7 && <span className="bg-card__star bg-card__star--t7">✦</span>}
    </div>
  );
}

function CardPortrait({ minion }) {
  const [errored, setErrored] = useState(false);
  const artUrl = minion.image_url && !minion.image_url.includes('/render/')
    ? minion.image_url
    : minion.image_url && minion.image_url.includes('/render/')
      ? null  // skip render urls — use art fallback
      : null;

  // Use 256x art URL directly
  const directArt = minion.render_id
    ? `https://art.hearthstonejson.com/v1/256x/${minion.render_id}.jpg`
    : null;

  const src = directArt || artUrl;

  if (src && !errored) {
    return (
      <img
        className="bg-card__portrait-img"
        src={src}
        alt={minion.name}
        draggable={false}
        onError={() => setErrored(true)}
      />
    );
  }
  // Fallback — big emoji + gradient bg
  const raceColor = RACE_COLORS[minion.race] || '#374151';
  return (
    <div className="bg-card__portrait-fallback"
      style={{ background: `radial-gradient(ellipse at 40% 35%, ${raceColor}88 0%, #0a0810 80%)` }}>
      <span className="bg-card__portrait-emoji">{RACE_EMOJI[minion.race] || '⚔️'}</span>
    </div>
  );
}

export default function MinionCard({
  minion, size = 'md', onAdd, onRemove,
  onStatChange, onMechanicToggle, boardTarget, isOnBoard = false, onMagnetize = null,
}) {
  const [editing, setEditing] = useState(null);
  const [editVal, setEditVal] = useState('');
  const [tip, setTip] = useState(false);

  const atk = minion.currentAttack ?? minion.attack;
  const hp  = minion.currentHealth ?? minion.health;
  const isGold = !!minion.isGold;
  const kws = ['divine_shield','taunt','cleave','poisonous','windfury','reborn','magnetic'].filter(k => minion[k] || minion.mechanics?.includes(k));

  const frame = TIER_FRAME[minion.tier] || TIER_FRAME[1];
  const rc = RACE_COLORS[minion.race] || '#374151';

  const startEdit = (stat, val, e) => { e.stopPropagation(); setEditing(stat); setEditVal(String(val)); };
  const commit = () => {
    if (editing && onStatChange) {
      const v = parseInt(editVal, 10);
      if (!isNaN(v)) onStatChange(minion.instanceId, boardTarget, editing === 'attack' ? 'currentAttack' : 'currentHealth', v);
    }
    setEditing(null);
  };

  return (
    <div
      className={['bg-card', `bg-card--${size}`, isGold ? 'bg-card--gold' : ''].filter(Boolean).join(' ')}
      style={{ '--frame-border': frame.border, '--frame-bg': frame.bg, '--frame-glow': frame.glow, '--star-color': frame.star, '--rc': rc }}
      onMouseEnter={() => setTip(true)}
      onMouseLeave={() => setTip(false)}
    >
      {isGold && <div className="bg-card__gold-shimmer" />}

      {/* ── Outer BG frame ── */}
      <div className="bg-card__frame">

        {/* Tier stars — top left badge */}
        <div className="bg-card__tier-badge">
          <TierStars tier={minion.tier} />
        </div>

        {/* Portrait oval */}
        <div className={`bg-card__portrait-wrap ${isGold ? 'bg-card__portrait-wrap--gold' : ''}`}>
          <div className="bg-card__portrait-oval">
            <CardPortrait minion={minion} />
          </div>
          {/* Divine shield ring */}
          {minion.divine_shield && <div className="bg-card__ds-aura" />}
        </div>

        {/* Name scroll */}
        <div className="bg-card__name-scroll">
          <div className="bg-card__name-text">
            {isGold && <span className="bg-card__name-gold">★</span>}
          {minion.magnetized && minion.magnetized.length > 0 && <span style={{fontSize:'.55em',color:'#f59e0b'}}> 🔩{minion.magnetized.length}</span>}
            {minion.name}
            {isGold && <span className="bg-card__name-gold">★</span>}
          </div>
        </div>

        {/* Description area */}
        {minion.text && (
          <div className="bg-card__desc">
            <span className="bg-card__desc-text">{minion.text}</span>
          </div>
        )}

        {/* Race tag */}
        {minion.race && (
          <div className="bg-card__race-tag" style={{ color: rc }}>
            {RACE_EMOJI[minion.race]} {minion.race !== 'Neutral' ? minion.race : ''}
          </div>
        )}

        {/* Attack gem */}
        <div
          className={`bg-card__gem bg-card__gem--atk ${isOnBoard ? 'bg-card__gem--edit' : ''}`}
          onClick={e => isOnBoard && startEdit('attack', atk, e)}
        >
          {editing === 'attack' && isOnBoard
            ? <input className="bg-card__gem-input" value={editVal}
                onChange={e => setEditVal(e.target.value)} onBlur={commit}
                onKeyDown={e => e.key === 'Enter' && commit()} autoFocus
                onClick={e => e.stopPropagation()} />
            : atk
          }
        </div>

        {/* Health gem */}
        <div
          className={`bg-card__gem bg-card__gem--hp ${isOnBoard ? 'bg-card__gem--edit' : ''}`}
          onClick={e => isOnBoard && startEdit('health', hp, e)}
        >
          {editing === 'health' && isOnBoard
            ? <input className="bg-card__gem-input" value={editVal}
                onChange={e => setEditVal(e.target.value)} onBlur={commit}
                onKeyDown={e => e.key === 'Enter' && commit()} autoFocus
                onClick={e => e.stopPropagation()} />
            : hp
          }
        </div>

        {/* Keywords row */}
        {kws.length > 0 && (
          <div className="bg-card__kws">
            {kws.map(k => (
              <span key={k}
                className={`bg-card__kw ${isOnBoard ? 'bg-card__kw--toggle' : ''}`}
                title={MECHANIC_LABELS[k]}
                onClick={e => { e.stopPropagation(); isOnBoard && onMechanicToggle?.(minion.instanceId, boardTarget, k); }}>
                {MECHANIC_ICONS[k]}
              </span>
            ))}
          </div>
        )}

        {/* Add / Remove button */}
        {!isOnBoard && onAdd && (
          <button className="bg-card__action bg-card__action--add"
            onClick={e => { e.stopPropagation(); onAdd(minion); }}>+</button>
        )}
        {isOnBoard && onRemove && (
          <button className="bg-card__action bg-card__action--rem"
            onClick={e => { e.stopPropagation(); onRemove(minion.instanceId, boardTarget); }}>×</button>
        )}
      </div>

      {/* ── Tooltip ── */}
      {tip && (
        <div className="bg-card__tip" style={{ '--rc': rc, '--tc': frame.border }}>
          <div className="bg-card__tip-name">
            {isGold && <span style={{ color: '#f4d03f' }}>★ </span>}
            {minion.name}
            {isGold && <span style={{ color: '#f4d03f' }}> ★</span>}
          </div>
          <div className="bg-card__tip-tier" style={{ color: frame.star }}>
            Таверна уровень {minion.tier}
          </div>
          {minion.race && (
            <div className="bg-card__tip-race" style={{ background: `${rc}22`, borderColor: `${rc}55`, color: rc }}>
              {RACE_EMOJI[minion.race]} {minion.race}
            </div>
          )}
          {minion.text && <div className="bg-card__tip-text">{minion.text}</div>}
          {kws.length > 0 && (
            <div className="bg-card__tip-kws">
              {kws.map(k => (
                <div key={k} className="bg-card__tip-kw">
                  <span>{MECHANIC_ICONS[k]}</span>
                  <span className="bg-card__tip-kw-name">{MECHANIC_LABELS[k]}</span>
                </div>
              ))}
            </div>
          )}
          <div className="bg-card__tip-stats">
            <span style={{ color: '#ef8b7e' }}>⚔ {atk}</span>
            <span style={{ color: '#7ed9a0' }}>♥ {hp}</span>
          </div>
          <div className="bg-card__tip-arrow" />
        </div>
      )}
    </div>
  );
}
