import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';

const API = '/api';

// ── Triplet → Gold ────────────────────────────────────────────────────────
// Правило: золотая карта = базовые статы карты × 2 (не текущие баффы)
// Копии могли быть заряфанными — это не влияет на результирующие статы голды
function makeGoldVersion(baseCard) {
  return {
    ...baseCard,
    isGold: true,
    // Всегда используем BASE стат карты × 2, игнорируем currentAttack/Health копий
    currentAttack: baseCard.attack * 2,
    currentHealth: baseCard.health * 2,
    divine_shield: baseCard.mechanics?.includes('divine_shield') || false,
    taunt:         baseCard.mechanics?.includes('taunt')         || false,
    cleave:        baseCard.mechanics?.includes('cleave')        || false,
    poisonous:     baseCard.mechanics?.includes('poisonous')     || false,
    windfury:      baseCard.mechanics?.includes('windfury')      || false,
    reborn:        baseCard.mechanics?.includes('reborn')        || false,
    magnetic:      baseCard.mechanics?.includes('magnetic')      || false,
  };
}

function checkAndMergeGold(board, newCard) {
  // Ищем 2 не-золотые копии той же карты
  const sameCards = board.filter(m => m.id === newCard.id && !m.isGold);
  if (sameCards.length >= 2) {
    const idsToRemove = sameCards.slice(0, 2).map(m => m.instanceId);
    const filtered = board.filter(m => !idsToRemove.includes(m.instanceId));
    // Золотая версия строится от базовой карты (newCard хранит base stats)
    const goldCard = makeGoldVersion(newCard);
    return { board: [...filtered, goldCard], wasGold: true };
  }
  return { board: [...board, newCard], wasGold: false };
}

export const useStore = create(
  persist(
    (set, get) => ({
      cards: [],
      cardsLoading: false,
      cardsError: null,
      filters: { tier: null, race: '', mechanic: '' },
      playerBoard: [],
      enemyBoard: [],
      simResult: null,
      simLoading: false,
      simError: null,
      activeTab: 'board',
      selectedBoardTarget: 'player',
      goldToast: null,

      fetchCards: async () => {
        set({ cardsLoading: true, cardsError: null });
        try {
          const { filters } = get();
          const params = {};
          if (filters.tier) params.tier = filters.tier;
          if (filters.race) params.race = filters.race;
          if (filters.mechanic) params.mechanic = filters.mechanic;
          const res = await axios.get(`${API}/cards/`, { params });
          set({ cards: res.data.cards, cardsLoading: false });
        } catch (e) {
          set({ cardsError: 'Failed to load cards', cardsLoading: false });
        }
      },

      setFilter: (key, value) => {
        set(s => ({ filters: { ...s.filters, [key]: value } }));
        get().fetchCards();
      },

      addToBoard: (card, target = 'player') => {
        const board = target === 'player' ? get().playerBoard : get().enemyBoard;
        if (board.length >= 7) return;

        const instance = {
          ...card,
          instanceId: `${card.id}-${Date.now()}-${Math.random()}`,
          isGold: false,
          divine_shield: card.mechanics?.includes('divine_shield') || false,
          taunt:         card.mechanics?.includes('taunt')         || false,
          cleave:        card.mechanics?.includes('cleave')        || false,
          poisonous:     card.mechanics?.includes('poisonous')     || false,
          windfury:      card.mechanics?.includes('windfury')      || false,
          reborn:        card.mechanics?.includes('reborn')        || false,
          magnetic:      card.mechanics?.includes('magnetic')      || false,
          // currentAttack/Health = базовые статы (не умноженные)
          currentAttack: card.attack,
          currentHealth: card.health,
        };

        const { board: newBoard, wasGold } = checkAndMergeGold(board, instance);
        if (target === 'player') set({ playerBoard: newBoard });
        else set({ enemyBoard: newBoard });

        if (wasGold) {
          set({ goldToast: `✨ ${card.name} стал ЗОЛОТЫМ!` });
          setTimeout(() => set({ goldToast: null }), 2500);
        }
      },

      removeFromBoard: (instanceId, target = 'player') => {
        if (target === 'player') {
          set(s => ({ playerBoard: s.playerBoard.filter(m => m.instanceId !== instanceId) }));
        } else {
          set(s => ({ enemyBoard: s.enemyBoard.filter(m => m.instanceId !== instanceId) }));
        }
      },

      updateMinionStat: (instanceId, target, stat, value) => {
        const board = target === 'player' ? 'playerBoard' : 'enemyBoard';
        set(s => ({
          [board]: s[board].map(m =>
            m.instanceId === instanceId ? { ...m, [stat]: Math.max(0, value) } : m
          )
        }));
      },

      toggleMinionMechanic: (instanceId, target, mechanic) => {
        const board = target === 'player' ? 'playerBoard' : 'enemyBoard';
        set(s => ({
          [board]: s[board].map(m =>
            m.instanceId === instanceId ? { ...m, [mechanic]: !m[mechanic] } : m
          )
        }));
      },

      reorderBoard: (target, oldIndex, newIndex) => {
        const board = target === 'player' ? 'playerBoard' : 'enemyBoard';
        set(s => {
          const arr = [...s[board]];
          const [moved] = arr.splice(oldIndex, 1);
          arr.splice(newIndex, 0, moved);
          return { [board]: arr };
        });
      },

      // ── Magnetic: прилипает к правому соседу ─────────────────────────
      magnetizeToRight: (instanceId, target) => {
        const boardKey = target === 'player' ? 'playerBoard' : 'enemyBoard';
        set(s => {
          const board = [...s[boardKey]];
          const srcIdx = board.findIndex(m => m.instanceId === instanceId);
          if (srcIdx === -1) return s;

          // Ищем ближайшего Мека СПРАВА
          let tgtIdx = -1;
          for (let i = srcIdx + 1; i < board.length; i++) {
            if (board[i].race === 'Mech' && !board[i].isMagnetized) {
              tgtIdx = i; break;
            }
          }
          // Если справа нет — ищем слева
          if (tgtIdx === -1) {
            for (let i = srcIdx - 1; i >= 0; i--) {
              if (board[i].race === 'Mech' && !board[i].isMagnetized) {
                tgtIdx = i; break;
              }
            }
          }
          if (tgtIdx === -1) return s; // нет Мека для прикрепления

          const src = board[srcIdx];
          const tgt = board[tgtIdx];

          // Мек поглощает статы и ключевые слова Magnetic-карты
          const merged = {
            ...tgt,
            currentAttack: (tgt.currentAttack ?? tgt.attack) + (src.currentAttack ?? src.attack),
            currentHealth: (tgt.currentHealth ?? tgt.health) + (src.currentHealth ?? src.health),
            divine_shield: tgt.divine_shield || src.divine_shield,
            taunt:         tgt.taunt         || src.taunt,
            windfury:      tgt.windfury       || src.windfury,
            reborn:        tgt.reborn         || src.reborn,
            poisonous:     tgt.poisonous      || src.poisonous,
            magnetizedWith: [...(tgt.magnetizedWith || []), src.name],
          };

          const newBoard = board.filter((_, i) => i !== srcIdx);
          const newTgtIdx = newBoard.findIndex(m => m.instanceId === tgt.instanceId);
          if (newTgtIdx !== -1) newBoard[newTgtIdx] = merged;

          return { [boardKey]: newBoard };
        });

        // Показываем тост
        set({ goldToast: '🔩 Намагничено!' });
        setTimeout(() => set({ goldToast: null }), 1500);
      },

      clearBoard: (target) => {
        if (target === 'player') set({ playerBoard: [] });
        else set({ enemyBoard: [] });
      },

      updateMinionWithSpell: (instanceId, target, spell) => {
        const board = target === 'player' ? 'playerBoard' : 'enemyBoard';
        set(s => ({
          [board]: s[board].map(m =>
            m.instanceId === instanceId ? spell.effect(m) : m
          )
        }));
      },

      simulate: async () => {
        const { playerBoard, enemyBoard } = get();
        if (!playerBoard.length || !enemyBoard.length) {
          set({ simError: 'Both boards must have at least one minion' });
          return;
        }
        set({ simLoading: true, simError: null, simResult: null });
        try {
          const toMinion = (m) => ({
            id: m.id,
            name: m.name,
            attack: m.currentAttack ?? m.attack,
            health: m.currentHealth ?? m.health,
            mechanics: m.mechanics || [],
            divine_shield: m.divine_shield || false,
            taunt:         m.taunt         || false,
            cleave:        m.cleave        || false,
            poisonous:     m.poisonous     || false,
            windfury:      m.windfury       || false,
            reborn:        m.reborn        || false,
          });
          const res = await axios.post(`${API}/simulate/battle`, {
            board_a: playerBoard.map(toMinion),
            board_b: enemyBoard.map(toMinion),
            iterations: 1000,
          });
          set({ simResult: res.data, simLoading: false });
        } catch (e) {
          set({ simError: 'Simulation failed', simLoading: false });
        }
      },

      setActiveTab:            (tab) => set({ activeTab: tab }),
      setSelectedBoardTarget:  (t)   => set({ selectedBoardTarget: t }),
      clearSimResult:          ()    => set({ simResult: null, simError: null }),
    }),
    {
      name: 'hs-bg-sandbox',
      partialState: (s) => ({ playerBoard: s.playerBoard, enemyBoard: s.enemyBoard }),
    }
  )
);
