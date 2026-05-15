"use client";

const SCALE = 3;
const NATIVE_H = 160;
const STRIP_H = NATIVE_H * SCALE; // 480 px — default strip height

interface Layer {
  src: string;
  nativeW: number; // sprite width at 1×
  durationS: number; // scroll period (0 = static)
  stripH?: number; // override strip height in px (defaults to STRIP_H)
  zIndex: number;
}

const layers: Layer[] = [
  // Static sky — full viewport, background-cover
  {
    src: "/assets/parallax_mountain_pack/layers/parallax-mountain-bg.png",
    nativeW: 272,
    durationS: 0,
    zIndex: 0,
  },

  // Far mountains — slowest. Strip is extra tall so the base always reaches
  // bottom: 0 regardless of viewport height, eliminating the bottom gap.
  {
    src: "/assets/parallax_mountain_pack/layers/parallax-mountain-montain-far.png",
    nativeW: 272,
    durationS: 80,
    stripH: 900,
    zIndex: 1,
  },

  // Nearer range
  {
    src: "/assets/parallax_mountain_pack/layers/parallax-mountain-mountains.png",
    nativeW: 544,
    durationS: 50,
    zIndex: 2,
  },

  // Background trees
  {
    src: "/assets/parallax_mountain_pack/layers/parallax-mountain-trees.png",
    nativeW: 544,
    durationS: 30,
    zIndex: 3,
  },

  // Foreground trees — fastest
  {
    src: "/assets/parallax_mountain_pack/layers/parallax-mountain-foreground-trees.png",
    nativeW: 544,
    durationS: 18,
    zIndex: 4,
  },
];

export default function ParallaxBackground() {
  return (
    <>
      {/* Inject per-layer keyframes as a plain <style> tag */}
      <style>{`
        ${layers
          .filter((l) => l.durationS > 0)
          .map(
            (l) => `
          @keyframes px-scroll-${l.zIndex} {
            from { background-position: 0 bottom; }
            to   { background-position: -${l.nativeW * SCALE}px bottom; }
          }`,
          )
          .join("\n")}
      `}</style>

      <div className="fixed inset-0" style={{ zIndex: 0, overflow: "hidden" }} aria-hidden="true">
        {layers.map((layer) => {
          const scaledW = layer.nativeW * SCALE;
          const stripH = layer.stripH ?? STRIP_H;
          const isStatic = layer.durationS === 0;

          if (isStatic) {
            return (
              <div
                key={layer.zIndex}
                style={{
                  position: "absolute",
                  inset: 0,
                  zIndex: layer.zIndex,
                  backgroundImage: `url(${layer.src})`,
                  backgroundSize: "cover",
                  backgroundPosition: "top center",
                  backgroundRepeat: "no-repeat",
                  imageRendering: "pixelated",
                }}
              />
            );
          }

          return (
            <div
              key={layer.zIndex}
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                bottom: 0,
                height: stripH,
                zIndex: layer.zIndex,
                backgroundImage: `url(${layer.src})`,
                backgroundRepeat: "repeat-x",
                backgroundSize: `${scaledW}px ${STRIP_H}px`,
                backgroundPosition: "0 bottom",
                imageRendering: "pixelated",
                animation: `px-scroll-${layer.zIndex} ${layer.durationS}s linear infinite`,
                willChange: "background-position",
              }}
            />
          );
        })}
      </div>
    </>
  );
}
