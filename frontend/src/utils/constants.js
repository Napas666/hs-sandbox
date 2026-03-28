export const RACES = ['Beast','Demon','Dragon','Elemental','Mech','Murloc','Naga','Pirate','Quilboar','Undead','Neutral'];

export const MECHANICS = ['divine_shield','taunt','cleave','poisonous','windfury','reborn','magnetic'];

export const MECHANIC_LABELS = {
  divine_shield: 'Divine Shield',
  taunt:         'Taunt',
  cleave:        'Cleave',
  poisonous:     'Poisonous',
  windfury:      'Windfury',
  reborn:        'Reborn',
  magnetic:      'Magnetic',
};

export const MECHANIC_ICONS = {
  divine_shield: '🛡️',
  taunt:         '🗡️',
  cleave:        '⚔️',
  poisonous:     '☠️',
  windfury:      '💨',
  reborn:        '🔄',
  magnetic:      '🔩',
};

export const RACE_COLORS = {
  Beast:     '#8b5e3c',
  Demon:     '#6b21a8',
  Dragon:    '#dc2626',
  Elemental: '#0891b2',
  Mech:      '#475569',
  Murloc:    '#0d9488',
  Naga:      '#4f7942',
  Pirate:    '#b45309',
  Quilboar:  '#9f1239',
  Undead:    '#6b7280',
  Neutral:   '#374151',
};

export const TIER_COLORS = {
  1: '#9ca3af',
  2: '#34d399',
  3: '#60a5fa',
  4: '#a78bfa',
  5: '#f59e0b',
  6: '#f87171',
  7: '#f4d03f',
};

export function getBoardStats(board) {
  return {
    totalAttack:  board.reduce((s,m) => s + (m.currentAttack ?? m.attack), 0),
    totalHealth:  board.reduce((s,m) => s + (m.currentHealth ?? m.health), 0),
    avgAttack:    board.length ? (board.reduce((s,m) => s + (m.currentAttack ?? m.attack), 0) / board.length).toFixed(1) : 0,
    avgHealth:    board.length ? (board.reduce((s,m) => s + (m.currentHealth ?? m.health), 0) / board.length).toFixed(1) : 0,
    races:        [...new Set(board.map(m => m.race).filter(Boolean))],
    divineShields: board.filter(m => m.divine_shield).length,
    taunts:       board.filter(m => m.taunt).length,
  };
}

// Add magnetic to mechanics
export const MECHANIC_ICONS_EXT = {
  ...{divine_shield:'🛡️',taunt:'🗡️',cleave:'⚔️',poisonous:'☠️',windfury:'💨',reborn:'🔄'},
  magnetic: '🔩',
};
export const MECHANIC_LABELS_EXT = {
  ...{divine_shield:'Divine Shield',taunt:'Taunt',cleave:'Cleave',poisonous:'Poisonous',windfury:'Windfury',reborn:'Reborn'},
  magnetic: 'Magnetic',
};
