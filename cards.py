import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone,timedelta
from typing import Dict
from deck import load_deck, save_deck
import heapq
import itertools


_seq = itertools.count

def _now() -> datetime:
    return datetime.now(timezone.utc)

def human_date(iso_ts: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_ts)
    except ValueError:
        return iso_ts
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")

@dataclass
class Card:
    id : str
    front : str
    back : str
    interval : int = 1
    ease_factor : float = 2.5
    step : int = 1
    due : str = _now().isoformat()
    first_time : bool = True

    @classmethod
    def from_dict(self, raw:Dict[str, object]) -> "Card":
        return self(**raw)
    
    def to_dict(self) -> Dict[str, object]:
        return asdict(self)
    
    @classmethod
    def new(self, front: str, back: str) -> "Card":
        return self(
            id = str(uuid.uuid4()),
            front = front,
            back = back,
            due = _now().isoformat(),
            first_time = True
        )
    
steps = {1: timedelta(minutes=1),
             1.5: timedelta(minutes=6),
             2: timedelta(minutes=10)}

#card scheduling algorithm modified SM-2
def update_schedule(card: Card, quality: int) -> None:
    now = _now()
    if quality <0 or quality > 3:
        raise ValueError("Quality must be between 0 and 3")
    if card.step < len(steps):
        learning_steps(card, quality)
    else:
        if quality == 0:
            card.step = 1
            learning_steps(card, quality)
        elif quality == 1:
            card.ease_factor -= 0.15
            card.interval = card.interval * 1.2
        elif quality == 2:
            card.interval = card.interval * card.ease_factor
        else:
            card.ease_factor += 0.15
            card.interval = card.interval * card.ease_factor * 1.3
    card.ease_factor = max(1.3, card.ease_factor)
    card.interval = round(card.interval)
    card.due = now + timedelta(day=card.interval)

#learning session & lapses
def learning_steps(card: Card, quality: int) -> None:
    now = _now
    step = card.step
    if step < len(steps):
        if quality < 0 or quality > 3:
            raise ValueError("qualitty must be between 0 to 3")
        if quality == 0:
            step = 1
        elif quality == 1:
            step += 0.5
        elif quality == 2:
            step += 1
        elif quality == 3:
            step = 3
            card.interval = 1
    card.due = now + steps[step]
    card.first_time = False

#add new card into decks
def add_card(front, back, deck_name: str):
    deck = load_deck(deck_name)
    card = Card.new(front = front, back = back)
    deck.append(card.to_dict())
    save_deck(deck_name, deck)

#start studying session
def study_deck(deck_name: str, limit, quality):
    cards_raw = load_deck(deck_name)
    cards = [Card.from_dict(c) for c in cards_raw]
    now = _now
    session_cards = []
    for c in cards:
        due_dt = datetime.fromisoformat(c.due)
        if due_dt <= now:
            heapq.heappush(session_cards, (due_dt, next(_seq),c))

    reviewed = 0
    while session_cards and (limit is None or reviewed < limit):
        _, _, card = heapq.heappop(session_cards)
        update_schedule(card, quality)
        if card.step < 3:
            new_due_dt = datetime.fromisoformat(card.due)
            heapq.heappush(session_cards, (new_due_dt,next(_seq), card))
        elif card.step == 3:
            reviewed +=1
        for idx, stored in enumerate(cards_raw):
            if stored["id"] == card.id:
                cards_raw[idx] = card.to_dict()
                break
