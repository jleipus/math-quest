"use client";

import { useState, useEffect } from "react";
import PlayerCard from "./components/PlayerCard";
import MathCard from "./components/MathCard";
import DrawingModal from "./components/DrawingModal";
import { Player, Card, Stroke, Difficulty } from "./types";
import { generateTasks, analyseAnswer } from "./services/api";

export default function Home() {
  const [player, setPlayer] = useState<Player>({
    name: "Player",
    health: 100,
    maxHealth: 100,
    avatar: "🧑",
  });

  const [enemy, setEnemy] = useState<Player>({
    name: "Enemy",
    health: 80,
    maxHealth: 100,
    avatar: "👾",
  });

  const [cards, setCards] = useState<Card[]>([]);
  const [isLoadingCards, setIsLoadingCards] = useState(true);
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Calculate damage based on difficulty
  const getDamageForDifficulty = (difficulty: Difficulty): number => {
    const damageMap: Record<Difficulty, number> = {
      easy: 8,
      medium: 15,
      hard: 25,
    };
    return damageMap[difficulty];
  };

  // Fetch tasks on mount
  useEffect(() => {
    const fetchTasks = async () => {
      setIsLoadingCards(true);
      try {
        // Fetch a mix of difficulties
        const easyTasks = await generateTasks({
          topic: "arithmetic",
          difficulty: "easy",
          count: 2,
        });
        const mediumTasks = await generateTasks({
          topic: "multiplication",
          difficulty: "medium",
          count: 2,
        });
        const hardTasks = await generateTasks({
          topic: "division",
          difficulty: "hard",
          count: 1,
        });

        const allTasks = [...easyTasks, ...mediumTasks, ...hardTasks];
        const cardsWithDamage: Card[] = allTasks.map((task) => ({
          ...task,
          damage: getDamageForDifficulty(task.difficulty),
        }));

        setCards(cardsWithDamage);
      } catch (error) {
        console.error("Error fetching tasks:", error);
      } finally {
        setIsLoadingCards(false);
      }
    };

    fetchTasks();
  }, []);

  const playCard = (card: Card) => {
    setSelectedCard(card);
    setFeedback(null);
  };

  const closeDrawingWindow = () => {
    setSelectedCard(null);
    setFeedback(null);
  };

  const handleSubmitAnswer = async (strokes: Stroke[]) => {
    if (!selectedCard) return;

    setIsSubmitting(true);
    setFeedback(null);

    try {
      const result = await analyseAnswer(selectedCard.task_id, strokes);

      if (result.message) {
        setFeedback(result.message);
      } else {
        console.log("No feedback message received.");
      }

      // If answer is correct, deal damage to enemy
      if (!result.has_issue) {
        setTimeout(() => {
          setEnemy((prev) => ({
            ...prev,
            health: Math.max(0, prev.health - selectedCard.damage),
          }));
          closeDrawingWindow();

          const index = cards.findIndex((card) => {
            card.task_id == selectedCard.task_id;
          });

          if (index > -1) {
            setCards((prev) => {
              return prev.splice(index, 1);
            });
          }
        }, 1000);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex h-screen flex-col overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-purple-950 p-5 text-white">
      {/* Top Section: Player and Enemy */}
      <div className="relative z-5 mb-auto flex justify-between gap-5">
        <PlayerCard player={player} />
        <PlayerCard player={enemy} isEnemy />
      </div>

      {/* Center Battle Area */}
      <div className="relative z-10 flex flex-1 items-center justify-center">
        <div className="text-center">
          <h1 className="mb-2 text-5xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 drop-shadow-lg">
            Math Battle
          </h1>
          <p className="text-lg text-gray-400">Choose a card to attack!</p>
        </div>
      </div>

      {/* Bottom Section: Cards */}
      <div className="relative z-10 rounded-2xl border-3 border-purple-900/50 bg-gradient-to-br from-slate-800/80 to-slate-900/80 p-5 shadow-2xl backdrop-blur-sm">
        <div className="flex justify-center gap-6">
          {isLoadingCards ? (
            <div className="flex items-center gap-3 text-gray-400">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-purple-500 border-t-transparent"></div>
              <span>Loading cards...</span>
            </div>
          ) : cards.length === 0 ? (
            <div className="text-gray-400">No cards available</div>
          ) : (
            cards.map((card) => (
              <MathCard
                key={card.task_id}
                card={card}
                onClick={() => playCard(card)}
              />
            ))
          )}
        </div>
      </div>

      {/* Drawing Window Modal */}
      {selectedCard && (
        <DrawingModal
          card={selectedCard}
          onClose={closeDrawingWindow}
          onSubmit={handleSubmitAnswer}
          isSubmitting={isSubmitting}
          feedback={feedback}
        />
      )}
    </div>
  );
}
