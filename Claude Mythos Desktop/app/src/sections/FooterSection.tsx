import { Sparkles, Github, ExternalLink, Heart } from "lucide-react";

export default function FooterSection() {
  return (
    <footer
      id="footer"
      className="relative py-20"
      style={{ zIndex: 10, background: "#0B0C10" }}
    >
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-12 flex items-center gap-2">
          <Sparkles className="h-4 w-4" style={{ color: "#FFD700" }} />
          <span
            className="text-xs font-medium tracking-[0.2em]"
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              color: "#F5F5F5",
            }}
          >
            GLASSWING
          </span>
        </div>

        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          <div>
            <h4
              className="mb-4 text-[10px] font-medium uppercase tracking-[0.2em]"
              style={{ fontFamily: "'Inter', sans-serif", color: "rgba(245,245,245,0.4)" }}
            >
              Model Status
            </h4>
            <ul className="space-y-2">
              <li>
                <span className="flex items-center gap-2 text-xs" style={{ color: "#F5F5F5" }}>
                  <span
                    className="inline-block h-1.5 w-1.5 rounded-full"
                    style={{ background: "#228B22" }}
                  />
                  Claude Sonnet 4 — Online
                </span>
              </li>
              <li>
                <span className="flex items-center gap-2 text-xs" style={{ color: "rgba(245,245,245,0.5)" }}>
                  <span
                    className="inline-block h-1.5 w-1.5 rounded-full"
                    style={{ background: "#228B22" }}
                  />
                  Neural Architecture — Active
                </span>
              </li>
              <li>
                <span className="flex items-center gap-2 text-xs" style={{ color: "rgba(245,245,245,0.5)" }}>
                  <span
                    className="inline-block h-1.5 w-1.5 rounded-full"
                    style={{ background: "#FFD700" }}
                  />
                  Memory Lattice — Syncing
                </span>
              </li>
            </ul>
          </div>

          <div>
            <h4
              className="mb-4 text-[10px] font-medium uppercase tracking-[0.2em]"
              style={{ fontFamily: "'Inter', sans-serif", color: "rgba(245,245,245,0.4)" }}
            >
              API Documentation
            </h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="#"
                  className="flex items-center gap-2 text-xs transition-colors hover:text-[#FFD700]"
                  style={{ color: "rgba(245,245,245,0.5)" }}
                >
                  <ExternalLink className="h-3 w-3" />
                  OpenRouter Integration
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="flex items-center gap-2 text-xs transition-colors hover:text-[#FFD700]"
                  style={{ color: "rgba(245,245,245,0.5)" }}
                >
                  <Github className="h-3 w-3" />
                  GitHub Repository
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="flex items-center gap-2 text-xs transition-colors hover:text-[#FFD700]"
                  style={{ color: "rgba(245,245,245,0.5)" }}
                >
                  <ExternalLink className="h-3 w-3" />
                  Changelog
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4
              className="mb-4 text-[10px] font-medium uppercase tracking-[0.2em]"
              style={{ fontFamily: "'Inter', sans-serif", color: "rgba(245,245,245,0.4)" }}
            >
              Telemetry
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between text-xs" style={{ color: "rgba(245,245,245,0.5)" }}>
                <span>Version</span>
                <span style={{ color: "#F5F5F5" }}>1.0.0-alpha</span>
              </div>
              <div className="flex justify-between text-xs" style={{ color: "rgba(245,245,245,0.5)" }}>
                <span>Build</span>
                <span style={{ color: "#F5F5F5" }}>glasswing-2026</span>
              </div>
              <div className="flex justify-between text-xs" style={{ color: "rgba(245,245,245,0.5)" }}>
                <span>Status</span>
                <span style={{ color: "#228B22" }}>Operational</span>
              </div>
            </div>
          </div>
        </div>

        <div
          className="mt-12 flex items-center justify-between border-t border-white/5 pt-6"
        >
          <p className="text-[10px]" style={{ color: "rgba(245,245,245,0.3)" }}>
            &copy; 2026 Claude Mythos (Project Glasswing). All rights reserved.
          </p>
          <p className="flex items-center gap-1 text-[10px]" style={{ color: "rgba(245,245,245,0.3)" }}>
            Crafted with <Heart className="h-3 w-3" style={{ color: "#FFD700" }} /> by AI
          </p>
        </div>
      </div>
    </footer>
  );
}
