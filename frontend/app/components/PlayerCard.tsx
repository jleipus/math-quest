import { Player } from "../types";

type PlayerCardProps = {
  player: Player;
  isEnemy?: boolean;
};

export default function PlayerCard({
  player,
  isEnemy = false,
}: PlayerCardProps) {
  const healthPercentage = (player.health / player.maxHealth) * 100;
  const borderColor = isEnemy ? "border-red-500" : "border-blue-500";
  const healthColor = isEnemy ? "bg-red-500" : "bg-green-500";
  const glowColor = isEnemy ? "shadow-red-500/20" : "shadow-blue-500/20";

  return (
    <div
      className={`group relative rounded-xl border-4 ${borderColor} bg-gradient-to-br from-slate-700 to-slate-800 p-5 shadow-2xl ${glowColor} transition-all`}
    >
      <div className="flex flex-col items-center">
        <div className="mb-3 rounded-full bg-slate-900 p-4 text-6xl shadow-lg">
          {player.avatar}
        </div>
        <h2 className="mb-3 text-2xl font-bold tracking-wide text-white drop-shadow-lg">
          {player.name}
        </h2>
        <div className="mb-2 text-sm font-semibold text-gray-300">
          HP: {player.health} / {player.maxHealth}
        </div>
        <div className="relative h-4 w-48 overflow-hidden rounded-full bg-gray-900 shadow-inner">
          <div
            className={`h-full ${healthColor} transition-all duration-500 ease-out shadow-lg`}
            style={{ width: `${healthPercentage}%` }}
          >
            <div className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
