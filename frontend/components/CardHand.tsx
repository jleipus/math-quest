"use client";

import type { Card as CardInfo } from "../lib/types";
import { canPlayCard } from "../lib/gameLogic";
import Card from "./Card";

type Props = {
  hand: CardInfo[];
  onClickCard: (card: CardInfo) => void;
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
        No cards - end your turn to draw a new hand.
      </div>
    );
  }

  return (
    <div className="flex flex-wrap justify-center gap-4 px-2">
      {hand.map((card) => (
        <Card
          key={card.card_id}
          card={card}
          onClick={onClickCard}
          playing={playingCardId === card.card_id}
          affordable={canPlayCard(energy, card)}
          energyCost={card.energy_cost}
        />
      ))}
    </div>
  );
}
