import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router";
import { useAuth } from "@/hooks/useAuth";
import { LogOut, User, Sparkles } from "lucide-react";

export default function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 100);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 nav-glass ${scrolled ? "scrolled" : ""}`}
      style={{ height: 80 }}
    >
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-6">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm font-medium tracking-[0.2em]"
          style={{
            fontFamily: "'Space Grotesk', sans-serif",
            color: scrolled ? "#F5F5F5" : "#1A1A1A",
          }}
        >
          <Sparkles className="h-4 w-4" />
          GLASSWING
        </Link>

        <div className="flex items-center gap-8">
          <button
            onClick={() => scrollToSection("capabilities")}
            className="hidden text-xs font-medium uppercase tracking-[0.15em] transition-colors hover:text-[#FFD700] md:block"
            style={{
              fontFamily: "'Inter', sans-serif",
              color: scrolled ? "rgba(245,245,245,0.7)" : "rgba(26,26,26,0.7)",
            }}
          >
            Capabilities
          </button>
          <button
            onClick={() => scrollToSection("terminal")}
            className="hidden text-xs font-medium uppercase tracking-[0.15em] transition-colors hover:text-[#FFD700] md:block"
            style={{
              fontFamily: "'Inter', sans-serif",
              color: scrolled ? "rgba(245,245,245,0.7)" : "rgba(26,26,26,0.7)",
            }}
          >
            Chronicle
          </button>
          <button
            onClick={() => scrollToSection("footer")}
            className="hidden text-xs font-medium uppercase tracking-[0.15em] transition-colors hover:text-[#FFD700] md:block"
            style={{
              fontFamily: "'Inter', sans-serif",
              color: scrolled ? "rgba(245,245,245,0.7)" : "rgba(26,26,26,0.7)",
            }}
          >
            Status
          </button>

          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <div
                className="flex items-center gap-2 rounded-full px-3 py-1.5"
                style={{
                  background: scrolled
                    ? "rgba(255,255,255,0.05)"
                    : "rgba(0,0,0,0.05)",
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              >
                {user?.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.name || "User"}
                    className="h-5 w-5 rounded-full"
                  />
                ) : (
                  <User className="h-4 w-4" style={{ color: scrolled ? "#F5F5F5" : "#1A1A1A" }} />
                )}
                <span
                  className="max-w-[80px] truncate text-xs"
                  style={{ color: scrolled ? "#F5F5F5" : "#1A1A1A" }}
                >
                  {user?.name || "User"}
                </span>
              </div>
              <button
                onClick={logout}
                className="rounded-full p-2 transition-colors hover:bg-red-500/10"
                title="Logout"
              >
                <LogOut className="h-4 w-4" style={{ color: scrolled ? "#F5F5F5" : "#1A1A1A" }} />
              </button>
            </div>
          ) : (
            <button
              onClick={() => navigate("/login")}
              className="rounded-full px-5 py-2 text-xs font-medium uppercase tracking-[0.1em] transition-all hover:scale-105"
              style={{
                fontFamily: "'Inter', sans-serif",
                background: "#1A1A1A",
                color: "#F5F5F5",
              }}
            >
              Deploy
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
