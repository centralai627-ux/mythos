import { relations } from "drizzle-orm";
import { users, conversations, messages, chatSettings } from "./schema";

export const usersRelations = relations(users, ({ many, one }) => ({
  conversations: many(conversations),
  chatSettings: one(chatSettings, {
    fields: [users.id],
    references: [chatSettings.userId],
  }),
}));

export const conversationsRelations = relations(conversations, ({ one, many }) => ({
  user: one(users, {
    fields: [conversations.userId],
    references: [users.id],
  }),
  messages: many(messages),
}));

export const messagesRelations = relations(messages, ({ one }) => ({
  conversation: one(conversations, {
    fields: [messages.conversationId],
    references: [conversations.id],
  }),
}));

export const chatSettingsRelations = relations(chatSettings, ({ one }) => ({
  user: one(users, {
    fields: [chatSettings.userId],
    references: [users.id],
  }),
}));
