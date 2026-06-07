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
    // A single row that scrolls sideways as soon as the cards no longer fit.
    <div className="flex gap-4 px-2 py-2 overflow-x-auto overscroll-x-contain px-scroll [justify-content:safe_center]">
      {hand.map((card) => (
        <div key={card.card_id} className="shrink-0">
          <Card
            card={card}
            onClick={onClickCard}
            playing={playingCardId === card.card_id}
            affordable={canPlayCard(energy, card)}
            energyCost={card.energy_cost}
          />
        </div>
      ))}
    </div>
  );
}
