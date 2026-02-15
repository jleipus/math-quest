import { Card, Difficulty } from "../types";

type MathCardProps = {
  card: Card;
  onClick: () => void;
};

const difficultyColors: Record<
  Difficulty,
  {
    gradient: string;
    border: string;
    glow: string;
    text: string;
  }
> = {
  easy: {
    gradient: "from-green-500 via-green-600 to-green-800",
    border: "border-green-400",
    glow: "hover:shadow-green-500/50",
    text: "text-green-200",
  },
  medium: {
    gradient: "from-yellow-500 via-orange-600 to-orange-800",
    border: "border-orange-400",
    glow: "hover:shadow-orange-500/50",
    text: "text-orange-200",
  },
  hard: {
    gradient: "from-red-500 via-red-600 to-red-800",
    border: "border-red-400",
    glow: "hover:shadow-red-500/50",
    text: "text-red-200",
  },
};

export default function MathCard({ card, onClick }: MathCardProps) {
  const colors = difficultyColors[card.difficulty];

  return (
    <button
      onClick={onClick}
      className={`group relative flex h-50 w-45 flex-col items-center justify-between overflow-hidden rounded-xl border-3 ${colors.border} bg-gradient-to-br ${colors.gradient} p-5 shadow-xl transition-all hover:-translate-y-3 hover:shadow-2xl ${colors.glow} active:translate-y-0 active:shadow-lg`}
    >
      {/* Card content */}
      <div className="relative z-10 flex h-full w-full flex-col items-center justify-between">
        {/* Topic Badge */}
        <div className="w-full rounded-lg bg-black/30 px-2 py-1 backdrop-blur-sm">
          <div className="text-center text-xs font-bold uppercase tracking-wide text-white/90">
            {card.topic}
          </div>
        </div>

        {/* Question */}
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-2xl font-bold text-white drop-shadow-lg">
            {card.question}
          </div>
        </div>

        {/* Damage */}
        <div className="flex w-full items-center justify-center">
          <div className="flex flex-col items-center gap-1">
            <div
              className={`text-xs font-semibold uppercase tracking-wider ${colors.text}`}
            >
              Damage
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-red-600 text-lg font-bold text-white shadow-lg">
              {card.damage}
            </div>
          </div>
        </div>
      </div>

      {/* Glow effect on hover */}
      <div className="absolute inset-0 rounded-xl opacity-0 transition-opacity group-hover:opacity-100 group-hover:animate-pulse">
        <div
          className={`absolute inset-0 blur-xl ${colors.border} opacity-30`}
        ></div>
      </div>
    </button>
  );
}
