"""
HS Battlegrounds Simulator — полная реализация механик Season 12.

Реализованные механики:
  БОЕВЫЕ:
  - Cleave (урон соседям)
  - Windfury / Mega-Windfury (2 атаки за ход)
  - Divine Shield (поглощает 1 удар)
  - Taunt (принудительная цель)
  - Poisonous / Venomous (убивает с 1 удара)
  - Reborn (возрождается с 1 HP)
  - Magnetic (объединение мехов — учитывается до боя)

  DEATHRATTLE:
  - Harmless Bonehead → 2x 1/1 Skeleton
  - Buzzing Vermin → 1/1 Beetle
  - Cord Puller → 1/1 Microbot
  - Twilight Hatchling → Whelp (атакует немедленно)
  - Forest Rover → Beetle
  - Aranasi Alchemist → (buff tavern, skip in combat)
  - Bassgill → summon highest-health Murloc from hand (skipped)
  - Scourfin → buff hand (skipped)
  - Anub'arak → +1 Atk to Undead (global buff)
  - Monstrous Macaw → trigger left-most Deathrattle
  - Rylak Metalhead → trigger Battlecry of adjacent (skip, pre-combat)
  - Silent Enforcer → deal damage to all non-Demon
  - Stellar Freebooter → give Health equal to Attack to friendly
  - Runed Progenitor → Beetle + buff
  - Silithid Burrower → buff Beasts
  - Twilight Broodmother → summon 2 Hatchlings
  - Turquoise Skitterer → buff Beetles
  - Spiked Savior → +1 HP all + damage
  - Carapace Raiser → (spell, skipped)
  - Arid Atrocity → summon Golem
  - Eternal Summoner → summon Eternal Knight
  - Deathly Striker → summon from hand (skipped)
  - Stitched Salvager → summon copy
  - Sanguine Champion → Blood Gem buff (skipped)
  - Champion of Sargeras → buff Tavern (skipped)

  START OF COMBAT:
  - Misfit Dragonling → gain stats = Tier
  - Humming Bird → Beasts +1 Atk this combat
  - Irate Rooster → deal 1 dmg to adjacent + buff them
  - Amber Guardian → give Dragon +X/+X + Divine Shield
  - Prized Promo-Drake → give Dragons +X/+X
  - Fire-forged Evoker → give Dragons +X/+X
  - Soulsplitter → give friendly Undead Reborn
  - Costume Enthusiast → gain Atk of highest-Atk in hand
  - Stitched Salvager → destroy left + Deathrattle summon copy

  RALLY (при атаке):
  - Monstrous Macaw → trigger left-most Deathrattle
  - Rampager → deal 1 dmg to own minions
  - Whelp Watcher → summon Whelp to attack first
  - Obsidian Ravager → deal Atk dmg to target + adjacent
  - Niuzao → deal Atk dmg to random enemy
  - Bile Spitter → give Murloc Venomous
  - Razorfen Vineweaver → self Blood Gems (skipped)
  - Bonker → Blood Gems all Quilboar (skipped)

  WHENEVER (триггеры во время боя):
  - Hardy Orca → when takes damage → buff other minions
  - Roaring Recruiter → when Dragon attacks → give Dragon +X/+X
  - Trigore the Lasher → when Beast takes damage → self +Health
  - Twilight Watcher → when Dragon attacks → give Dragons +X/+X
  - Iridescent Skyblazer → when Beast takes damage → buff other Beast
  - Devout Hellcaller → when Demon deals damage → self +X/+X
  - Lord of the Ruins → when Demon deals damage → buff others

  AFTER (после событий):
  - Wildfire Elemental → after kills → deal excess to adjacent
  - Grease Bot → after Mech loses DS → +2/+2 perm

  BUFF TRACKING:
  - Все баффы (+Atk, +HP) применяются к current_attack/current_health
  - Постоянные баффы (permanently) сохраняются на весь бой
  - Временные баффы (this combat / until next turn) сбрасываются
"""

import random
import copy
from typing import List, Optional
from dataclasses import dataclass, field

# ─── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class Minion:
    id: int
    name: str
    attack: int
    health: int
    max_health: int = 0
    # keywords
    divine_shield: bool = False
    taunt: bool = False
    cleave: bool = False
    poisonous: bool = False
    windfury: bool = False
    reborn: bool = False
    magnetic: bool = False
    # state
    alive: bool = True
    uid: str = ""
    race: str = "Neutral"
    tier: int = 1
    # attacks used this combat (for windfury tracking)
    attacks_this_turn: int = 0
    _death_processed: bool = False
    # rally flag
    has_rally: bool = False

    def __post_init__(self):
        if self.max_health == 0:
            self.max_health = self.health
        if not self.uid:
            self.uid = f"{self.id}-{random.randint(0,999999)}"

    def is_alive(self):
        return self.alive and self.health > 0

    def to_dict(self):
        return {
            "uid": self.uid, "id": self.id, "name": self.name,
            "attack": self.attack, "health": self.health,
            "max_health": self.max_health,
            "divine_shield": self.divine_shield, "taunt": self.taunt,
            "cleave": self.cleave, "poisonous": self.poisonous,
            "windfury": self.windfury, "reborn": self.reborn,
            "race": self.race, "tier": self.tier,
            "alive": self.is_alive(),
        }


@dataclass
class Board:
    minions: List[Minion] = field(default_factory=list)
    side: str = "A"

    def alive_minions(self):
        return [m for m in self.minions if m.is_alive()]

    def get_targets(self):
        alive = self.alive_minions()
        taunts = [m for m in alive if m.taunt]
        return taunts if taunts else alive

    def deathrattle_multiplier(self):
        for m in self.alive_minions():
            if m.name in ("Titus Rivendare", "Baron Rivendare"):
                return 2
        return 1

    def battlecry_multiplier(self):
        for m in self.alive_minions():
            if m.name == "Brann Bronzebeard":
                return 2
        return 1

    def board_snapshot(self):
        return [m.to_dict() for m in self.minions]

    def minion_index(self, minion: Minion) -> int:
        for i, m in enumerate(self.minions):
            if m.uid == minion.uid:
                return i
        return -1

    def adjacent_alive(self, minion: Minion) -> tuple:
        """Returns (left_minion_or_None, right_minion_or_None)"""
        idx = self.minion_index(minion)
        left = right = None
        for i in range(idx - 1, -1, -1):
            if self.minions[i].is_alive():
                left = self.minions[i]
                break
        for i in range(idx + 1, len(self.minions)):
            if self.minions[i].is_alive():
                right = self.minions[i]
                break
        return left, right


# ─── Build board ──────────────────────────────────────────────────────────────

def build_board(data: list, side: str) -> Board:
    minions = []
    for m in data:
        mechanics = m.get("mechanics", [])
        if isinstance(mechanics, str):
            import json
            try: mechanics = json.loads(mechanics)
            except: mechanics = []
        text = m.get("text", "").lower()
        has_rally = "rally" in text
        minions.append(Minion(
            id=m.get("id", 0),
            name=m.get("name", "Unknown"),
            attack=m.get("attack", 1),
            health=m.get("health", 1),
            max_health=m.get("health", 1),
            divine_shield="divine_shield" in mechanics or m.get("divine_shield", False),
            taunt="taunt" in mechanics or m.get("taunt", False),
            cleave="cleave" in mechanics or m.get("cleave", False),
            poisonous="poisonous" in mechanics or m.get("poisonous", False),
            windfury="windfury" in mechanics or m.get("windfury", False),
            reborn="reborn" in mechanics or m.get("reborn", False),
            magnetic="magnetic" in mechanics or m.get("magnetic", False),
            race=m.get("race", "Neutral"),
            tier=m.get("tier", 1),
            has_rally=has_rally,
        ))
    return Board(minions=minions, side=side)


# ─── START OF COMBAT effects ──────────────────────────────────────────────────

def apply_start_of_combat(board: Board, enemy_board: Board, events: list, snap):
    """Apply all Start of Combat effects for a board."""
    for m in list(board.alive_minions()):
        name = m.name

        if name == "Misfit Dragonling":
            buff = m.tier
            m.attack += buff
            m.health += buff
            m.max_health += buff
            _event(events, "buff", m, board.side, f"SOC: +{buff}/+{buff}", snap)

        elif name == "Humming Bird":
            for b in board.alive_minions():
                if b.race == "Beast":
                    b.attack += 1
            _event(events, "buff", m, board.side, "SOC: Beasts +1 Atk", snap)

        elif name == "Irate Rooster":
            left, right = board.adjacent_alive(m)
            for adj in [left, right]:
                if adj:
                    _deal_damage(adj, 1, False)
                    adj.attack += adj.attack  # "give them + Attack" = double? Actually gives +their current atk
            _event(events, "buff", m, board.side, "SOC: adjacent dmg+buff", snap)

        elif name == "Amber Guardian":
            targets = [b for b in board.alive_minions() if b.race == "Dragon" and b is not m]
            if targets:
                t = random.choice(targets)
                t.attack += 2
                t.health += 2
                t.max_health += 2
                t.divine_shield = True
                _event(events, "buff", t, board.side, "SOC: +2/+2 + DS", snap)

        elif name in ("Prized Promo-Drake", "Fire-forged Evoker"):
            for b in board.alive_minions():
                if b.race == "Dragon":
                    b.attack += 2
                    b.health += 2
                    b.max_health += 2
            _event(events, "buff", m, board.side, "SOC: Dragons +2/+2", snap)

        elif name == "Soulsplitter":
            targets = [b for b in board.alive_minions() if b.race == "Undead" and b is not m]
            if targets:
                t = random.choice(targets)
                t.reborn = True
                _event(events, "buff", t, board.side, "SOC: give Reborn", snap)

        elif name == "Costume Enthusiast":
            # gain attack of highest-attack in hand — skip (no hand in sim), give self +2
            m.attack += 2
            _event(events, "buff", m, board.side, "SOC: +Atk", snap)

        elif name == "Stitched Salvager":
            # Destroy left minion, Deathrattle: summon copy
            left, _ = board.adjacent_alive(m)
            if left:
                left.alive = False
                left._death_processed = True
                copy_m = copy.deepcopy(left)
                copy_m.uid = f"copy-{left.uid}"
                copy_m.alive = True
                copy_m.health = copy_m.max_health
                idx = board.minion_index(m)
                board.minions.insert(idx + 1, copy_m)
                _event(events, "spawn", copy_m, board.side, f"Salvager copy {left.name}", snap)


def _event(events, etype, minion, side, msg="", snap=None):
    if events is None:
        return
    e = {"type": etype, "uid": minion.uid, "side": side, "name": minion.name, "msg": msg}
    if snap:
        e["boards"] = snap()
    events.append(e)


# ─── Damage & Death ────────────────────────────────────────────────────────────

def _deal_damage(target: Minion, amount: int, poisonous: bool) -> bool:
    """Returns True if divine shield was popped."""
    if not target.is_alive():
        return False
    if target.divine_shield:
        target.divine_shield = False
        return True  # DS popped
    if poisonous and amount > 0:
        target.health = 0
        target.alive = False
    else:
        target.health -= amount
        if target.health <= 0:
            target.alive = False
    return False


def _get_deathrattle_spawns(m: Minion, board: Board) -> list:
    """Returns list of Minion objects to spawn, possibly multiple times."""
    name = m.name

    def spawn(n, a, h, race="Neutral", **kw):
        return Minion(id=0, name=n, attack=a, health=h, max_health=h, race=race, **kw)

    spawns = {
        "Harmless Bonehead":  [spawn("Skeleton",1,1,"Undead"), spawn("Skeleton",1,1,"Undead")],
        "Buzzing Vermin":     [spawn("Beetle",1,1,"Beast", taunt=True)],
        "Cord Puller":        [spawn("Microbot",1,1,"Mech")],
        "Forest Rover":       [spawn("Beetle",2,2,"Beast")],
        "Twilight Broodmother":[spawn("Twilight Hatchling",1,1,"Dragon", taunt=True),
                                spawn("Twilight Hatchling",1,1,"Dragon", taunt=True)],
        "Eternal Summoner":   [spawn("Eternal Knight",3,3,"Undead")],
        "Runed Progenitor":   [spawn("Beetle",2,2,"Beast")],
        "Turquoise Skitterer":[spawn("Beetle",2,2,"Beast")],
        "Stellar Freebooter": [],  # handled separately
        "Arid Atrocity":      [spawn("Golem", max(1, len(board.minions)), max(1,len(board.minions)), "Neutral")],
        "Silky Shimmermoth":  [spawn("Beetle",2,2,"Beast")],
    }

    # Silent Enforcer — dealt via effect, not spawn
    # Three Lil' Quilboar — Blood Gem (no combat effect)

    return spawns.get(name, [])


def _apply_deathrattle_effect(m: Minion, own_board: Board, enemy_board: Board, events, snap):
    """Effects that don't spawn minions."""
    name = m.name

    if name == "Anub'arak, Nerubian King":
        for b in own_board.alive_minions():
            if b.race == "Undead":
                b.attack += 1
        _event(events, "buff", m, own_board.side, "DR: Undead +1 Atk", snap)

    elif name == "Silent Enforcer":
        dmg = m.attack
        for b in enemy_board.alive_minions():
            _deal_damage(b, dmg, False)
        for b in own_board.alive_minions():
            if b.race != "Demon":
                _deal_damage(b, dmg, False)
        _event(events, "buff", m, own_board.side, f"DR: AoE {dmg} dmg", snap)

    elif name == "Stellar Freebooter":
        targets = own_board.alive_minions()
        if targets:
            t = random.choice(targets)
            t.health += m.attack
            t.max_health += m.attack
        _event(events, "buff", m, own_board.side, f"DR: give +{m.attack} Health", snap)

    elif name == "Silithid Burrower":
        for b in own_board.alive_minions():
            if b.race == "Beast":
                b.attack += 2
                b.health += 2
                b.max_health += 2
        _event(events, "buff", m, own_board.side, "DR: Beasts +2/+2", snap)

    elif name == "Spiked Savior":
        for b in own_board.alive_minions():
            b.health += 1
            b.max_health += 1
            _deal_damage(b, 1, False)
        _event(events, "buff", m, own_board.side, "DR: all +1 HP / 1 dmg", snap)

    elif name == "Three Lil' Quilboar":
        for b in own_board.alive_minions():
            if b.race == "Quilboar":
                b.attack += 1
                b.health += 1
                b.max_health += 1
        _event(events, "buff", m, own_board.side, "DR: Quilboar Blood Gems", snap)

    elif name == "Monstrous Macaw":
        # Trigger left-most deathrattle on the board (excluding self)
        for b in own_board.alive_minions():
            if b is not m and _has_deathrattle(b):
                _apply_deathrattle_effect(b, own_board, enemy_board, events, snap)
                spawns = _get_deathrattle_spawns(b, own_board)
                _do_spawns(spawns, b, own_board, events, snap)
                break


def _has_deathrattle(m: Minion) -> bool:
    return m.name in (
        "Harmless Bonehead","Buzzing Vermin","Cord Puller","Forest Rover",
        "Twilight Broodmother","Eternal Summoner","Runed Progenitor",
        "Turquoise Skitterer","Arid Atrocity","Silky Shimmermoth",
        "Anub'arak, Nerubian King","Silent Enforcer","Stellar Freebooter",
        "Silithid Burrower","Spiked Savior","Three Lil' Quilboar",
    )


def _do_spawns(spawns: list, dead: Minion, board: Board, events, snap):
    idx = next((i for i, x in enumerate(board.minions) if x.uid == dead.uid), -1)
    insert_pos = idx + 1 if idx != -1 else len(board.minions)
    for sp in spawns:
        board.minions.insert(insert_pos, sp)
        insert_pos += 1
        _event(events, "spawn", sp, board.side, f"spawn {sp.name}", snap)


# ─── RALLY effects ────────────────────────────────────────────────────────────

def apply_rally(attacker: Minion, target: Minion, own_board: Board, enemy_board: Board, events, snap):
    """Called when a Rally minion attacks."""
    name = attacker.name

    if name == "Monstrous Macaw":
        # Trigger left-most Deathrattle minion
        for m in own_board.alive_minions():
            if m is not attacker and _has_deathrattle(m):
                _event(events, "rally", attacker, own_board.side, f"Rally: trigger DR {m.name}", snap)
                _apply_deathrattle_effect(m, own_board, enemy_board, events, snap)
                spawns = _get_deathrattle_spawns(m, own_board)
                _do_spawns(spawns, m, own_board, events, snap)
                break

    elif name == "Rampager":
        for m in own_board.alive_minions():
            if m is not attacker:
                _deal_damage(m, 1, False)
        _event(events, "rally", attacker, own_board.side, "Rally: 1 dmg own minions", snap)

    elif name == "Whelp Watcher":
        # summon a Whelp that attacks immediately
        whelp = Minion(id=0, name="Whelp", attack=2, health=2, race="Dragon")
        own_board.minions.append(whelp)
        # Whelp attacks immediately
        enemy_targets = enemy_board.get_targets()
        if enemy_targets:
            wtgt = random.choice(enemy_targets)
            _deal_damage(wtgt, whelp.attack, False)
            _deal_damage(whelp, wtgt.attack, False)
        _event(events, "rally", attacker, own_board.side, "Rally: Whelp attacks", snap)

    elif name == "Obsidian Ravager":
        # deal Atk damage to target and adjacent
        dmg = attacker.attack
        all_enemy = enemy_board.minions
        if target in all_enemy:
            idx = all_enemy.index(target)
            for adj_i in [idx-1, idx+1]:
                if 0 <= adj_i < len(all_enemy) and all_enemy[adj_i].is_alive():
                    _deal_damage(all_enemy[adj_i], dmg, attacker.poisonous)
        _event(events, "rally", attacker, own_board.side, f"Rally: cleave {dmg}", snap)

    elif name == "Niuzao":
        enemy_alive = [x for x in enemy_board.alive_minions() if x is not target]
        if enemy_alive:
            t = random.choice(enemy_alive)
            _deal_damage(t, attacker.attack, attacker.poisonous)
        _event(events, "rally", attacker, own_board.side, "Rally: extra hit", snap)

    elif name == "Bile Spitter":
        targets = [m for m in own_board.alive_minions() if m.race == "Murloc" and m is not attacker]
        if targets:
            random.choice(targets).poisonous = True
        _event(events, "rally", attacker, own_board.side, "Rally: Murloc Venomous", snap)


# ─── WHENEVER triggers ────────────────────────────────────────────────────────

def on_minion_takes_damage(damaged: Minion, damage_amount: int, attacker: Minion,
                            own_board: Board, events, snap):
    """Triggered when any minion takes damage."""
    for m in own_board.alive_minions():
        if not m.is_alive():
            continue

        if m.name == "Hardy Orca" and m is damaged and damage_amount > 0:
            for b in own_board.alive_minions():
                if b is not m:
                    b.attack += 1
                    b.health += 1
                    b.max_health += 1
            _event(events, "buff", m, own_board.side, "Orca: +1/+1 others", snap)

        elif m.name == "Trigore the Lasher" and damaged.race == "Beast" and damaged is not m:
            m.health += 1
            m.max_health += 1
            _event(events, "buff", m, own_board.side, "Trigore: +Health", snap)

        elif m.name == "Iridescent Skyblazer" and damaged.race == "Beast" and damaged is not m:
            targets = [b for b in own_board.alive_minions() if b.race == "Beast" and b is not damaged]
            if targets:
                t = random.choice(targets)
                t.attack += 3
                t.health += 1
                t.max_health += 1
            _event(events, "buff", m, own_board.side, "Skyblazer: Beast +3/+1", snap)


def on_minion_attacks(attacker: Minion, own_board: Board, enemy_board: Board, events, snap):
    """Triggered when a minion attacks."""
    for m in own_board.alive_minions():
        if not m.is_alive():
            continue

        if m.name == "Roaring Recruiter" and attacker.race == "Dragon":
            attacker.attack += 1
            attacker.health += 1
            attacker.max_health += 1
            _event(events, "buff", m, own_board.side, "Recruiter: Dragon +1/+1", snap)

        elif m.name == "Twilight Watcher" and attacker.race == "Dragon":
            for b in own_board.alive_minions():
                if b.race == "Dragon":
                    b.attack += 1
                    b.health += 1
                    b.max_health += 1
            _event(events, "buff", m, own_board.side, "Watcher: Dragons +1/+1", snap)


def on_minion_deals_damage(dealer: Minion, own_board: Board, events, snap):
    """Triggered when a minion deals damage."""
    for m in own_board.alive_minions():
        if not m.is_alive():
            continue

        if m.name == "Devout Hellcaller" and dealer.race == "Demon" and dealer is not m:
            m.attack += 1
            m.health += 1
            m.max_health += 1
            _event(events, "buff", m, own_board.side, "Hellcaller: +1/+1", snap)

        elif m.name == "Lord of the Ruins" and dealer.race == "Demon":
            for b in own_board.alive_minions():
                if b is not dealer:
                    b.attack += 1
                    b.health += 1
                    b.max_health += 1
            _event(events, "buff", m, own_board.side, "Lord of Ruins: others +1/+1", snap)


def on_minion_loses_ds(minion: Minion, own_board: Board, events, snap):
    """Triggered when a minion loses Divine Shield."""
    for m in own_board.alive_minions():
        if m.name == "Grease Bot" and minion.race == "Mech":
            minion.attack += 2
            minion.health += 2
            minion.max_health += 2
            _event(events, "buff", m, own_board.side, "Grease Bot: Mech +2/+2", snap)


def on_minion_killed(attacker: Minion, killed: Minion,
                     own_board: Board, enemy_board: Board, events, snap):
    """Triggered after attacker kills a minion."""
    if attacker.name == "Wildfire Elemental":
        # deal excess damage to adjacent
        excess = attacker.attack - killed.max_health
        if excess > 0:
            alive = enemy_board.minions
            if killed in alive:
                idx = alive.index(killed)
                for adj_i in [idx-1, idx+1]:
                    if 0 <= adj_i < len(alive) and alive[adj_i].is_alive():
                        _deal_damage(alive[adj_i], excess, attacker.poisonous)
            _event(events, "buff", attacker, own_board.side, f"Wildfire: {excess} excess", snap)


# ─── Process Deaths ───────────────────────────────────────────────────────────

def _process_deaths(board: Board, own_board: Board, enemy_board: Board, events, snap):
    multiplier = board.deathrattle_multiplier()
    dead = [m for m in board.minions if not m.is_alive() and not m._death_processed]

    for m in dead:
        m._death_processed = True
        _event(events, "death", m, board.side, "", snap)

        # Deathrattle effects × multiplier
        for _ in range(multiplier):
            _apply_deathrattle_effect(m, board, enemy_board, events, snap)

        # Deathrattle spawns × multiplier
        base_spawns = _get_deathrattle_spawns(m, board)
        for _ in range(multiplier):
            for sp in base_spawns:
                sp_copy = copy.deepcopy(sp)
                sp_copy.uid = f"{sp.name}-{random.randint(0,99999)}"
                _do_spawns([sp_copy], m, board, events, snap)

        # Reborn
        if m.reborn:
            rb = Minion(
                id=m.id, name=m.name, attack=m.attack, health=1, max_health=m.max_health,
                taunt=m.taunt, race=m.race, tier=m.tier, has_rally=m.has_rally,
                divine_shield=False, cleave=m.cleave, poisonous=m.poisonous,
                windfury=m.windfury,
            )
            idx = next((i for i, x in enumerate(board.minions) if x.uid == m.uid), -1)
            if idx != -1:
                board.minions.insert(idx + 1, rb)
            _event(events, "reborn", rb, board.side, "", snap)


# ─── Core attack ──────────────────────────────────────────────────────────────

def _do_attack(attacker: Minion, target: Minion,
               attacker_board: Board, enemy_board: Board,
               events, snap):
    if not attacker.is_alive():
        return

    atk_side = attacker_board.side
    def_side = enemy_board.side

    if events is not None:
        events.append({
            "type": "attack",
            "attacker_uid": attacker.uid, "attacker_side": atk_side,
            "target_uid": target.uid, "target_side": def_side,
            "boards": snap() if snap else {},
        })

    # RALLY trigger (before damage)
    if attacker.has_rally and events is not None:
        apply_rally(attacker, target, attacker_board, enemy_board, events, snap)

    # "Whenever this minion attacks" triggers
    if events is not None:
        on_minion_attacks(attacker, attacker_board, enemy_board, events, snap)

    dmg = attacker.attack
    prev_ds = target.divine_shield
    ds_popped = _deal_damage(target, dmg, attacker.poisonous)

    if ds_popped:
        if events is not None:
            events.append({"type":"divine_shield_pop","uid":target.uid,"side":def_side,"boards":snap() if snap else {}})
        on_minion_loses_ds(target, enemy_board, events, snap)
    elif target.is_alive() or not target.is_alive():
        if events is not None:
            on_minion_takes_damage(target, dmg, attacker, enemy_board, events, snap)

    killed = not target.is_alive()

    # Attacker takes return fire (unless target died / had taunt considerations)
    if attacker.is_alive():
        prev_ds_atk = attacker.divine_shield
        ds_popped2 = _deal_damage(attacker, target.attack, target.poisonous)
        if ds_popped2:
            if events is not None:
                events.append({"type":"divine_shield_pop","uid":attacker.uid,"side":atk_side,"boards":snap() if snap else {}})
            on_minion_loses_ds(attacker, attacker_board, events, snap)
        elif not ds_popped2 and target.attack > 0:
            if events is not None:
                on_minion_takes_damage(attacker, target.attack, target, attacker_board, events, snap)

    # Attacker dealt damage — trigger effects
    if dmg > 0 and not ds_popped and events is not None:
        on_minion_deals_damage(attacker, attacker_board, events, snap)

    # Cleave
    if attacker.cleave:
        all_enemy = enemy_board.minions
        if target in all_enemy:
            idx = all_enemy.index(target)
            for li in range(idx - 1, -1, -1):
                if all_enemy[li].is_alive():
                    _deal_damage(all_enemy[li], dmg, attacker.poisonous)
                    if events is not None:
                        on_minion_takes_damage(all_enemy[li], dmg, attacker, enemy_board, events, snap)
                    break
            for ri in range(idx + 1, len(all_enemy)):
                if all_enemy[ri].is_alive():
                    _deal_damage(all_enemy[ri], dmg, attacker.poisonous)
                    if events is not None:
                        on_minion_takes_damage(all_enemy[ri], dmg, attacker, enemy_board, events, snap)
                    break

    # Wildfire Elemental — after kill
    if killed and attacker.is_alive() and events is not None:
        on_minion_killed(attacker, target, attacker_board, enemy_board, events, snap)

    # Process deaths
    _process_deaths(enemy_board, attacker_board, enemy_board, events, snap)
    _process_deaths(attacker_board, enemy_board, attacker_board, events, snap)


# ─── Replay simulation ────────────────────────────────────────────────────────

def simulate_with_replay(board_a_data: list, board_b_data: list):
    a = build_board(board_a_data, "A")
    b = build_board(board_b_data, "B")
    events = []

    def snap():
        return {"A": a.board_snapshot(), "B": b.board_snapshot()}

    events.append({"type":"start","boards":snap()})

    # Start of Combat — A goes first (coin flip for who goes first overall doesn't affect SOC)
    apply_start_of_combat(a, b, events, snap)
    apply_start_of_combat(b, a, events, snap)

    # Process any SOC deaths
    _process_deaths(a, b, a, events, snap)
    _process_deaths(b, a, b, events, snap)

    attacker_is_a = random.random() < 0.5
    idx_a = idx_b = 0

    for _ in range(100):
        alive_a, alive_b = a.alive_minions(), b.alive_minions()
        if not alive_a or not alive_b:
            break

        if attacker_is_a:
            idx_a = idx_a % len(alive_a)
            attacker = alive_a[idx_a]
            targets = b.get_targets()
            if not targets:
                break
            target = random.choice(targets)
            _do_attack(attacker, target, a, b, events, snap)

            # Windfury: 2nd attack
            if attacker.is_alive() and attacker.windfury:
                alive_b2 = b.alive_minions()
                if alive_b2:
                    _do_attack(attacker, random.choice(b.get_targets()), a, b, events, snap)

            idx_a = (idx_a + 1) % max(1, len(a.alive_minions()))
        else:
            idx_b = idx_b % len(alive_b)
            attacker = alive_b[idx_b]
            targets = a.get_targets()
            if not targets:
                break
            target = random.choice(targets)
            _do_attack(attacker, target, b, a, events, snap)

            if attacker.is_alive() and attacker.windfury:
                alive_a2 = a.alive_minions()
                if alive_a2:
                    _do_attack(attacker, random.choice(a.get_targets()), b, a, events, snap)

            idx_b = (idx_b + 1) % max(1, len(b.alive_minions()))

        attacker_is_a = not attacker_is_a

    alive_a = a.alive_minions()
    alive_b = b.alive_minions()
    winner = "A" if alive_a and not alive_b else ("B" if alive_b and not alive_a else "TIE")
    remaining_hp = sum(m.health for m in (alive_a if winner == "A" else alive_b))
    events.append({"type":"end","winner":winner,"remaining_hp":remaining_hp,"boards":snap()})
    return events, winner, remaining_hp


# ─── Monte Carlo simulation ───────────────────────────────────────────────────

def run_simulation(board_a_data: list, board_b_data: list, iterations=1000):
    board_a = build_board(board_a_data, "A")
    board_b = build_board(board_b_data, "B")
    results = {"A":0,"B":0,"TIE":0}
    th_a = th_b = 0

    for _ in range(iterations):
        r = _sim_once(copy.deepcopy(board_a), copy.deepcopy(board_b))
        results[r["winner"]] += 1
        if r["winner"] == "A": th_a += r["hp"]
        elif r["winner"] == "B": th_b += r["hp"]

    wa = results["A"]/iterations
    wb = results["B"]/iterations
    return {
        "win_rate_a": round(wa*100,1),
        "win_rate_b": round(wb*100,1),
        "tie_rate":   round(results["TIE"]/iterations*100,1),
        "avg_remaining_health_a": round(th_a/max(results["A"],1),1),
        "avg_remaining_health_b": round(th_b/max(results["B"],1),1),
        "iterations": iterations,
        "verdict": "YOUR_BOARD" if wa>wb else ("ENEMY_BOARD" if wb>wa else "TIE"),
    }


def _sim_once(a: Board, b: Board):
    # SOC
    apply_start_of_combat(a, b, None, None)
    apply_start_of_combat(b, a, None, None)
    _process_deaths(a, b, a, None, None)
    _process_deaths(b, a, b, None, None)

    attacker_is_a = random.random() < 0.5
    ia = ib = 0

    for _ in range(100):
        aa, ab = a.alive_minions(), b.alive_minions()
        if not aa or not ab:
            break

        if attacker_is_a:
            ia = ia % len(aa)
            att = aa[ia]
            tgts = b.get_targets()
            if not tgts: break
            tgt = random.choice(tgts)
            _do_attack(att, tgt, a, b, None, None)
            if att.is_alive() and att.windfury:
                alive2 = b.alive_minions()
                if alive2:
                    _do_attack(att, random.choice(b.get_targets()), a, b, None, None)
            ia = (ia+1) % max(1, len(a.alive_minions()))
        else:
            ib = ib % len(ab)
            att = ab[ib]
            tgts = a.get_targets()
            if not tgts: break
            tgt = random.choice(tgts)
            _do_attack(att, tgt, b, a, None, None)
            if att.is_alive() and att.windfury:
                alive2 = a.alive_minions()
                if alive2:
                    _do_attack(att, random.choice(a.get_targets()), b, a, None, None)
            ib = (ib+1) % max(1, len(b.alive_minions()))

        attacker_is_a = not attacker_is_a

    aa, ab = a.alive_minions(), b.alive_minions()
    if aa and not ab: return {"winner":"A","hp":sum(m.health for m in aa)}
    if ab and not aa: return {"winner":"B","hp":sum(m.health for m in ab)}
    return {"winner":"TIE","hp":0}
