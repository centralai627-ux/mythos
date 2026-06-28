import { Sparkles, ArrowLeft } from "lucide-react";
import { Link } from "react-router";

function getOAuthUrl() {
  const kimiAuthUrl = import.meta.env.VITE_KIMI_AUTH_URL;
  const appID = import.meta.env.VITE_APP_ID;
  const redirectUri = `${window.location.origin}/api/oauth/callback`;
  const state = btoa(redirectUri);

  const url = new URL(`${kimiAuthUrl}/api/oauth/authorize`);
  url.searchParams.set("client_id", appID);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "profile");
  url.searchParams.set("state", state);

  return url.toString();
}

export default function Login() {
  return (
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{ background: "#0B0C10" }}
    >
      <div className="w-full max-w-sm">
        <Link
          to="/"
          className="mb-8 flex items-center gap-2 text-xs uppercase tracking-[0.15em] transition-colors hover:text-[#FFD700]"
          style={{ color: "rgba(245,245,245,0.5)" }}
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Conduit
        </Link>

        <div className="glass-panel p-8" style={{ borderColor: "rgba(255,215,0,0.15)" }}>
          <div className="mb-6 text-center">
            <div
              className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full"
              style={{
                background: "rgba(255,215,0,0.08)",
                border: "1px solid rgba(255,215,0,0.2)",
              }}
            >
              <Sparkles className="h-6 w-6" style={{ color: "#FFD700" }} />
            </div>
            <h1
              className="mb-1 text-sm font-medium uppercase tracking-[0.15em]"
              style={{ fontFamily: "'Space Grotesk', sans-serif", color: "#F5F5F5" }}
            >
              Deploy Session
            </h1>
            <p className="text-xs" style={{ color: "rgba(245,245,245,0.4)" }}>
              Authenticate to access the Glasswing conduit
            </p>
          </div>

          <button
            onClick={() => {
              window.location.href = getOAuthUrl();
            }}
            className="w-full rounded-full px-6 py-3 text-xs font-medium uppercase tracking-[0.1em] transition-all hover:scale-[1.02] active:scale-[0.98]"
            style={{
              background: "#FFD700",
              color: "#1A1A1A",
              fontFamily: "'Inter', sans-serif",
            }}
          >
            <span className="flex items-center justify-center gap-2">
              <Sparkles className="h-3.5 w-3.5" />
              Sign in with Kimi
            </span>
          </button>

          <p className="mt-4 text-center text-[10px]" style={{ color: "rgba(245,245,245,0.3)" }}>
            Secure OAuth 2.0 authentication via Kimi Platform
          </p>
        </div>
      </div>
    </div>
  );
}
