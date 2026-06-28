import { authRouter } from "./auth-router";
import { chatRouter } from "./chat-router";
import { settingsRouter } from "./settings-router";
import { createRouter, publicQuery } from "./middleware";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),
  auth: authRouter,
  chat: chatRouter,
  settings: settingsRouter,
});

export type AppRouter = typeof appRouter;
