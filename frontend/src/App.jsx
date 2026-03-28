import React, { useEffect, useState } from 'react';
import Board from './components/Board/Board';
import CardLibrary from './components/CardLibrary/CardLibrary';
import BattleSimulator from './components/BattleSimulator/BattleSimulator';
import BattleArena from './components/BattleArena/BattleArena';
import SpellPanel from './components/SpellPanel/SpellPanel';
import { useStore } from './store/useStore';
import './App.css';

export default function App() {
  const { activeTab, setActiveTab, fetchCards, goldToast, playerBoard, enemyBoard } = useStore();
  const [showArena, setShowArena] = useState(false);

  useEffect(() => { fetchCards(); }, []);

  const canFight = playerBoard.length > 0 && enemyBoard.length > 0;

  return (
    <div className="app">
      <div className="app-bg">
        <div className="bg-orb bg-orb--1" />
        <div className="bg-orb bg-orb--2" />
        <div className="bg-orb bg-orb--3" />
        <div className="bg-grid" />
      </div>

      {goldToast && <div className="gold-toast animate-fade-in">{goldToast}</div>}
      {showArena && <BattleArena onClose={() => setShowArena(false)} />}

      <header className="app-header">
        <div className="header-brand">
          <div className="header-logo">⚔️</div>
          <div className="header-text">
            <h1 className="header-title">BG Sandbox</h1>
            <span className="header-sub">Hearthstone Battlegrounds Simulator</span>
          </div>
        </div>
        <nav className="header-nav">
          <button className={`nav-tab ${activeTab === 'board' ? 'nav-tab--active' : ''}`} onClick={() => setActiveTab('board')}>
            🏟️ Board Builder
          </button>
          <button className={`nav-tab ${activeTab === 'simulate' ? 'nav-tab--active' : ''}`} onClick={() => setActiveTab('simulate')}>
            🎲 Simulator
          </button>
        </nav>

        {/* Watch battle button */}
        <button
          className={`watch-battle-btn ${canFight ? 'watch-battle-btn--ready' : ''}`}
          onClick={() => canFight && setShowArena(true)}
          disabled={!canFight}
          title={canFight ? 'Watch the battle play out!' : 'Add minions to both boards first'}
        >
          ⚔️ Watch Battle
        </button>

        <div className="header-patch">
          <span className="patch-badge">Patch 34.6</span>
        </div>
      </header>

      <main className="app-main">
        {activeTab === 'board' ? (
          <div className="layout-board">
            <aside className="panel panel--library"><CardLibrary /></aside>
            <section className="panel panel--board">
              <div className="board-section-header">
                <h2 className="section-title">🏟️ Board Builder</h2>
                <p className="section-hint">Click card to add · Drag to reorder · Click stats to edit · Hover for description · 3 copies = ✨ Golden</p>
              </div>
              <Board />
            </section>
            <aside className="panel panel--spells">
              <SpellPanel />
            </aside>
          </div>
        ) : (
          <div className="layout-simulate">
            <aside className="panel panel--library"><CardLibrary /></aside>
            <section className="panel panel--board">
              <div className="board-section-header">
                <h2 className="section-title">🏟️ Boards</h2>
                <p className="section-hint">Build both boards, then simulate or watch live</p>
              </div>
              <Board />
            </section>
            <aside className="panel panel--simulator"><BattleSimulator /></aside>
          </div>
        )}
      </main>
    </div>
  );
}
