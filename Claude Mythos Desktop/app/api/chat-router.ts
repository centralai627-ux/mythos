import { z } from "zod";
import { createRouter, authedQuery } from "./middleware";
import {
  findConversationsByUserId,
  findConversationById,
  findMessagesByConversationId,
  createConversation,
  deleteConversation,
  createMessage,
  updateConversationTitle,
  findOrCreateChatSettings,
} from "./queries/conversations";
import { pollForCompletion } from "./services/openrouter";

export const chatRouter = createRouter({
  listConversations: authedQuery.query(async ({ ctx }) => {
    return findConversationsByUserId(ctx.user.id);
  }),

  getConversation: authedQuery
    .input(z.object({ id: z.number() }))
    .query(async ({ ctx, input }) => {
      const conversation = await findConversationById(input.id, ctx.user.id);
      if (!conversation) return null;
      const msgs = await findMessagesByConversationId(input.id);
      return { ...conversation, messages: msgs };
    }),

  createConversation: authedQuery
    .input(
      z.object({
        title: z.string().optional(),
        model: z.string().optional(),
      }).optional()
    )
    .mutation(async ({ ctx, input }) => {
      return createConversation(
        ctx.user.id,
        input?.title,
        input?.model
      );
    }),

  deleteConversation: authedQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ ctx, input }) => {
      return deleteConversation(input.id, ctx.user.id);
    }),

  sendMessage: authedQuery
    .input(
      z.object({
        conversationId: z.number(),
        content: z.string().min(1),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const conversation = await findConversationById(
        input.conversationId,
        ctx.user.id
      );
      if (!conversation) {
        throw new Error("Conversation not found");
      }

      const userMessage = await createMessage(
        input.conversationId,
        "user",
        input.content
      );

      const allMessages = await findMessagesByConversationId(input.conversationId);
      const settings = await findOrCreateChatSettings(ctx.user.id);

      const chatHistory = allMessages.map((m) => ({
        role: m.role as "user" | "assistant" | "system",
        content: m.content,
      }));

      const { content, tokensUsed } = await pollForCompletion(
        chatHistory,
        conversation.model,
        parseFloat(settings.temperature?.toString() || "0.7"),
        settings.systemPrompt
      );

      const assistantMessage = await createMessage(
        input.conversationId,
        "assistant",
        content,
        tokensUsed
      );

      if (allMessages.length <= 2) {
        const title = input.content.slice(0, 50) + (input.content.length > 50 ? "..." : "");
        await updateConversationTitle(input.conversationId, ctx.user.id, title);
      }

      return { userMessage, assistantMessage };
    }),
});
