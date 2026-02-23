"use client";

import type { Card as CardType } from "../lib/types";
import Card from "./Card";

type Props = {
  hand: CardType[];
  onClickCard: (card: CardType) => void; // Opens the task modal for any card
  playingCardId: string | null;
  energy: number;
};

export default function CardHand({ hand, onClickCard, playingCardId, energy }: Props) {
  if (hand.length === 0) {
    return (
      <div
        className="font-pixel flex h-52 items-center justify-center text-sm"
        style={{ color: "var(--px-text-dim)" }}
      >
        No cards — end your turn to draw a new hand.
      </div>
    );
  }

  return (
    <div className="flex flex-wrap justify-center gap-4 px-2">
      {hand.map((card, i) => (
        <Card
          key={card.card_id}
          card={card}
          index={i + 1}
          onClick={onClickCard}
          playing={playingCardId === card.card_id}
          affordable={energy >= card.energy_cost}
          energyCost={card.energy_cost}
        />
      ))}
    </div>
  );
}
