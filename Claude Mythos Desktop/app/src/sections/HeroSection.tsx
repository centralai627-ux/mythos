import { useEffect, useRef } from "react";
import { ChevronDown } from "lucide-react";

export default function HeroSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!textRef.current) return;
      const scrollY = window.scrollY;
      const progress = Math.min(scrollY / window.innerHeight, 1);
      textRef.current.style.transform = `translateY(${-progress * 100}px)`;
      textRef.current.style.opacity = `${1 - progress * 1.5}`;
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToCapabilities = () => {
    const el = document.getElementById("capabilities");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section
      ref={sectionRef}
      className="relative flex min-h-screen items-center justify-center"
      style={{ zIndex: 10 }}
    >
      <div
        ref={textRef}
        className="flex flex-col items-center text-center px-6"
        style={{ willChange: "transform, opacity" }}
      >
        <p
          className="mb-4 text-xs uppercase tracking-[0.3em]"
          style={{
            fontFamily: "'Inter', sans-serif",
            color: "rgba(26, 26, 26, 0.6)",
          }}
        >
          PROJECT MYTHOS // CLAUDE 4
        </p>

        <h1
          className="mb-6 font-light uppercase text-glow-gold"
          style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: "clamp(3rem, 8vw, 10rem)",
            letterSpacing: "-0.02em",
            lineHeight: 1.05,
            color: "#1A1A1A",
            textShadow: "0 2px 30px rgba(255,215,0,0.15)",
          }}
        >
          Thought
          <br />
          Conduit
        </h1>

        <p
          className="max-w-md text-sm leading-relaxed"
          style={{
            fontFamily: "'Inter', sans-serif",
            color: "rgba(26, 26, 26, 0.65)",
          }}
        >
          A living interface bridging human intuition and deep architectural reasoning.
        </p>

        <button
          onClick={scrollToCapabilities}
          className="mt-12 flex flex-col items-center gap-2 transition-all hover:translate-y-1"
          style={{ color: "rgba(26, 26, 26, 0.4)" }}
        >
          <span className="text-[10px] uppercase tracking-[0.2em]">Explore</span>
          <ChevronDown className="h-4 w-4 animate-bounce" />
        </button>
      </div>
    </section>
  );
}
