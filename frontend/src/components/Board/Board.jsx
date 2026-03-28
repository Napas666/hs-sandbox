import React from 'react';
import {
  DndContext, closestCenter, PointerSensor, useSensor, useSensors,
} from '@dnd-kit/core';
import {
  SortableContext, horizontalListSortingStrategy, useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import MinionCard from '../UI/MinionCard';
import { useStore } from '../../store/useStore';
import { getBoardStats } from '../../utils/constants';
import './Board.css';

function SortableMinion({ minion, boardTarget, onRemove, onStatChange, onMechanicToggle, onMagnetize }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: minion.instanceId });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 50 : 1,
  };

  const isMagnetic = minion.magnetic || minion.mechanics?.includes('magnetic');

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="sortable-wrapper">
      <MinionCard
        minion={minion}
        size="md"
        isOnBoard
        boardTarget={boardTarget}
        onRemove={onRemove}
        onStatChange={onStatChange}
        onMechanicToggle={onMechanicToggle}
      />
      {/* Magnetic button — клик прилипает к правому Меку */}
      {isMagnetic && (
        <button
          className="mag-btn"
          title="Намагнитить к правому Меку"
          onClick={e => { e.stopPropagation(); onMagnetize(minion.instanceId, boardTarget); }}
        >
          🔩 Attach
        </button>
      )}
      {/* Показываем к чему прикреплено */}
      {minion.magnetizedWith?.length > 0 && (
        <div className="mag-info" title={`Magnetized: ${minion.magnetizedWith.join(', ')}`}>
          🔩×{minion.magnetizedWith.length}
        </div>
      )}
    </div>
  );
}

function BoardPanel({ label, target, board, isActive }) {
  const { removeFromBoard, updateMinionStat, toggleMinionMechanic, reorderBoard, clearBoard, setSelectedBoardTarget, magnetizeToRight } = useStore();
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));
  const stats = getBoardStats(board);

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over?.id) {
      const oldIndex = board.findIndex(m => m.instanceId === active.id);
      const newIndex = board.findIndex(m => m.instanceId === over.id);
      reorderBoard(target, oldIndex, newIndex);
    }
  };

  return (
    <div className={`board-panel ${isActive ? 'board-panel--active' : ''}`}
      onClick={() => setSelectedBoardTarget(target)}>
      <div className="board-panel__header">
        <h3 className="board-panel__title">{label}</h3>
        <div className="board-panel__meta">
          <span className="board-count">{board.length}/7</span>
          {board.length > 0 && (
            <button className="clear-btn" onClick={e => { e.stopPropagation(); clearBoard(target); }}>Clear</button>
          )}
        </div>
      </div>

      {board.length > 0 && (
        <div className="board-stats">
          <div className="bstat"><span>⚔</span><span className="bstat__val">{stats.totalAttack}</span><span className="bstat__lbl">ATK</span></div>
          <div className="bstat"><span>♥</span><span className="bstat__val">{stats.totalHealth}</span><span className="bstat__lbl">HP</span></div>
          {stats.divineShields > 0 && <div className="bstat"><span>🛡️</span><span className="bstat__val">{stats.divineShields}</span></div>}
          {stats.taunts > 0 && <div className="bstat"><span>🗡️</span><span className="bstat__val">{stats.taunts}</span></div>}
          {stats.races.map(r => <div key={r} className="bstat bstat--race"><span>{r}</span></div>)}
        </div>
      )}

      <div className="board-slots">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={board.map(m => m.instanceId)} strategy={horizontalListSortingStrategy}>
            {board.map(minion => (
              <SortableMinion
                key={minion.instanceId}
                minion={minion}
                boardTarget={target}
                onRemove={removeFromBoard}
                onStatChange={updateMinionStat}
                onMechanicToggle={toggleMinionMechanic}
                onMagnetize={magnetizeToRight}
              />
            ))}
          </SortableContext>
        </DndContext>
        {Array.from({ length: Math.max(0, 7 - board.length) }).map((_, i) => (
          <div key={`empty-${i}`} className="board-slot--empty"><span>+</span></div>
        ))}
      </div>

      {isActive && board.length < 7 && (
        <div className="board-hint">← Нажми карту в библиотеке чтобы добавить · 🔩 = намагнитить к правому Меку</div>
      )}
    </div>
  );
}

export default function Board() {
  const { playerBoard, enemyBoard, selectedBoardTarget } = useStore();
  return (
    <div className="board-container">
      <BoardPanel label="⚔ Your Board" target="player" board={playerBoard} isActive={selectedBoardTarget === 'player'} />
      <div className="board-vs">VS</div>
      <BoardPanel label="💀 Enemy Board" target="enemy" board={enemyBoard} isActive={selectedBoardTarget === 'enemy'} />
    </div>
  );
}
