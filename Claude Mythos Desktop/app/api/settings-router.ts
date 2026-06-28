import { z } from "zod";
import { createRouter, authedQuery } from "./middleware";
import {
  findOrCreateChatSettings,
  updateChatSettings,
} from "./queries/conversations";

export const settingsRouter = createRouter({
  get: authedQuery.query(async ({ ctx }) => {
    return findOrCreateChatSettings(ctx.user.id);
  }),

  update: authedQuery
    .input(
      z.object({
        defaultModel: z.string().optional(),
        theme: z.enum(["light", "dark", "auto"]).optional(),
        temperature: z.string().optional(),
        systemPrompt: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const updateData: Record<string, unknown> = {};
      if (input.defaultModel !== undefined) updateData.defaultModel = input.defaultModel;
      if (input.theme !== undefined) updateData.theme = input.theme;
      if (input.temperature !== undefined) updateData.temperature = input.temperature;
      if (input.systemPrompt !== undefined) updateData.systemPrompt = input.systemPrompt;

      return updateChatSettings(ctx.user.id, updateData);
    }),
});
