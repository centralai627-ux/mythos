import { useEffect, useRef } from "react";
import { Brain, Clock, Database } from "lucide-react";

interface GlassPanelProps {
  title: string;
  description: string;
  image: string;
  icon: React.ReactNode;
  rotationY: number;
  translateZ: number;
  floatDelay: number;
}

function GlassPanel({
  title,
  description,
  image,
  icon,
  rotationY,
  translateZ,
  floatDelay,
}: GlassPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const panel = panelRef.current;
    if (!panel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            panel.style.opacity = "1";
            panel.style.transform = `perspective(1200px) rotateY(${rotationY}deg) translateZ(${translateZ}px) translateY(0)`;
          }
        });
      },
      { threshold: 0.2 }
    );

    observer.observe(panel);
    return () => observer.disconnect();
  }, [rotationY, translateZ]);

  return (
    <div
      ref={panelRef}
      className="glass-panel overflow-hidden float-organic"
      style={{
        opacity: 0,
        transform: `perspective(1200px) rotateY(${rotationY}deg) translateZ(${translateZ}px) translateY(40px)`,
        transition: "all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        animationDelay: `${floatDelay}s`,
        maxWidth: 420,
        width: "100%",
      }}
    >
      <div className="relative h-52 overflow-hidden">
        <img
          src={image}
          alt={title}
          className="h-full w-full object-cover transition-transform duration-700 hover:scale-110"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(to bottom, transparent 40%, rgba(11,12,16,0.9))",
          }}
        />
        <div className="absolute bottom-3 left-4 flex items-center gap-2">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full"
            style={{ background: "rgba(255,215,0,0.15)", border: "1px solid rgba(255,215,0,0.3)" }}
          >
            {icon}
          </div>
        </div>
      </div>
      <div className="p-5">
        <h3
          className="mb-2 text-sm font-medium uppercase tracking-[0.15em]"
          style={{
            fontFamily: "'Space Grotesk', sans-serif",
            color: "#F5F5F5",
          }}
        >
          {title}
        </h3>
        <p
          className="text-xs leading-relaxed"
          style={{
            fontFamily: "'Inter', sans-serif",
            color: "rgba(245, 245, 245, 0.55)",
          }}
        >
          {description}
        </p>
      </div>
    </div>
  );
}

export default function FeatureShowcase() {
  return (
    <section
      id="capabilities"
      className="relative py-32"
      style={{ zIndex: 10, minHeight: "150vh" }}
    >
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-20 text-center">
          <p
            className="mb-3 text-xs uppercase tracking-[0.3em]"
            style={{
              fontFamily: "'Inter', sans-serif",
              color: "rgba(255, 215, 0, 0.6)",
            }}
          >
            Neural Architecture
          </p>
          <h2
            className="mb-4 font-light uppercase"
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "clamp(2rem, 4vw, 4rem)",
              letterSpacing: "-0.02em",
              color: "#F5F5F5",
            }}
          >
            Capabilities
          </h2>
          <p
            className="mx-auto max-w-lg text-sm"
            style={{
              fontFamily: "'Inter', sans-serif",
              color: "rgba(245, 245, 245, 0.5)",
            }}
          >
            Three pillars of cognitive architecture, each designed to push the boundaries of what an AI can perceive, reason, and remember.
          </p>
        </div>

        <div className="flex flex-col items-center gap-12 lg:flex-row lg:items-start lg:justify-center">
          <GlassPanel
            title="Crystalline Memory"
            description="Infinite-context memory architecture that retains every detail across conversations. Information is stored in a lattice structure, enabling instant retrieval of any past interaction with crystalline precision."
            image="/images/panel-memory.jpg"
            icon={<Database className="h-4 w-4" style={{ color: "#FFD700" }} />}
            rotationY={-5}
            translateZ={50}
            floatDelay={0}
          />

          <GlassPanel
            title="Adaptive Reasoning"
            description="Dynamic reasoning engine that adjusts its cognitive depth based on query complexity. From quick pattern matching to multi-step logical deduction, the system scales its mental architecture in real-time."
            image="/images/panel-reasoning.jpg"
            icon={<Brain className="h-4 w-4" style={{ color: "#FFD700" }} />}
            rotationY={5}
            translateZ={100}
            floatDelay={2}
          />

          <GlassPanel
            title="Temporal Awareness"
            description="Chronological intelligence that understands the flow of time, trends, and causality. It can trace the evolution of ideas, predict future patterns, and contextualize every query within the proper temporal framework."
            image="/images/panel-timeline.jpg"
            icon={<Clock className="h-4 w-4" style={{ color: "#FFD700" }} />}
            rotationY={0}
            translateZ={75}
            floatDelay={4}
          />
        </div>
      </div>
    </section>
  );
}
