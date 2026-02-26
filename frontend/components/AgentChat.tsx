"use client";

type Props = {
  messages: string[];
  loading: boolean;
};

export default function AgentChat({ messages, loading }: Props) {
  return (
    <div
      style={{
        background: "rgba(40,15,40,0.8)",
        border: "2px solid var(--px-panel-border)",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        flex: 1,
        minHeight: 0,
      }}
    >
      {/* Bot icon and name */}
      <div className="mb-3 flex items-center gap-2" style={{ flexShrink: 0 }}>
        <span style={{ fontSize: 16 }}>🤖</span>
        <span className="font-pixel text-xs" style={{ color: "var(--px-pink)" }}>
          MiniGuide
        </span>
      </div>

      {/* Scrollable message list */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          minHeight: 0,
        }}
      >
        {/* If no messages */}
        {messages.length === 0 && !loading && (
          <p className="font-pixel text-xs leading-loose" style={{ color: "var(--px-text-dim)" }}>
            Ask for a hint and MiniGuide will help you here.
          </p>
        )}

        {/* If messages are present */}
        {messages.map((msg, i) => (
          <div
            key={i}
            className="animate-slide-in font-pixel text-xs leading-loose"
            style={{
              background: "#2a0d26",
              border: "2px solid #4a2040",
              padding: "10px 14px",
              color: "var(--px-text)",
              flexShrink: 0,
            }}
          >
            {msg}
          </div>
        ))}

        {/* If waiting for API response */}
        {loading && (
          <div
            className="font-pixel animate-pixel-pulse text-xs"
            style={{ color: "var(--px-text-dim)" }}
          >
            ▌ Thinking…
          </div>
        )}
      </div>
    </div>
  );
}
