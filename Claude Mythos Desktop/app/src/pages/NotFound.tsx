import { Link } from "react-router";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{ background: "#0B0C10" }}
    >
      <div className="text-center">
        <p
          className="mb-2 text-xs uppercase tracking-[0.3em]"
          style={{ color: "rgba(255, 215, 0, 0.6)", fontFamily: "'Inter', sans-serif" }}
        >
          Signal Lost
        </p>
        <h1
          className="mb-4 font-light"
          style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: "clamp(4rem, 10vw, 8rem)",
            color: "#F5F5F5",
            letterSpacing: "-0.02em",
            lineHeight: 1,
          }}
        >
          404
        </h1>
        <p className="mb-8 text-sm" style={{ color: "rgba(245,245,245,0.5)" }}>
          The requested conduit endpoint does not exist in this neural architecture.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-full px-6 py-2.5 text-xs font-medium uppercase tracking-[0.1em] transition-all hover:scale-105"
          style={{ background: "rgba(255,215,0,0.15)", border: "1px solid rgba(255,215,0,0.3)", color: "#FFD700" }}
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Return to Origin
        </Link>
      </div>
    </div>
  );
}
