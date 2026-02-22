"use client";

import type { Card as CardType } from "../lib/types";
import { ENERGY_COST } from "../lib/types";
import Card from "./Card";

type Props = {
  hand: CardType[];
  /** Called when a locked card is clicked — opens the task modal */
  onClickCard: (card: CardType) => void;
  /** Called when an unlocked card is clicked — plays it immediately */
  onPlayCard: (card: CardType) => void;
  playingCardId: string | null;
  energy: number;
};

export default function CardHand({ hand, onClickCard, onPlayCard, playingCardId, energy }: Props) {
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
      {hand.map((card, i) => {
        const cost = ENERGY_COST[card.task.difficulty];
        const affordable = energy >= cost;
        return (
          <Card
            key={card.card_id}
            card={card}
            index={i + 1}
            onClickCard={affordable ? onClickCard : () => {}}
            onPlayCard={onPlayCard}
            playing={playingCardId === card.card_id}
            affordable={affordable}
            energyCost={cost}
          />
        );
      })}
    </div>
  );
}
