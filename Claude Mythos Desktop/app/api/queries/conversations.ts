import { getDb } from "./connection";
import { conversations, messages, chatSettings } from "@db/schema";
import { eq, desc, and } from "drizzle-orm";

export async function findConversationsByUserId(userId: number) {
  const db = getDb();
  return db
    .select()
    .from(conversations)
    .where(eq(conversations.userId, userId))
    .orderBy(desc(conversations.updatedAt));
}

export async function findConversationById(id: number, userId: number) {
  const db = getDb();
  const [conversation] = await db
    .select()
    .from(conversations)
    .where(and(eq(conversations.id, id), eq(conversations.userId, userId)));
  return conversation || null;
}

export async function findMessagesByConversationId(conversationId: number) {
  const db = getDb();
  return db
    .select()
    .from(messages)
    .where(eq(messages.conversationId, conversationId))
    .orderBy(messages.createdAt);
}

export async function createConversation(userId: number, title?: string, model?: string) {
  const db = getDb();
  const [result] = await db.insert(conversations).values({
    userId,
    title: title || "New Conversation",
    model: model || "anthropic/claude-sonnet-4",
  });
  const [conversation] = await db
    .select()
    .from(conversations)
    .where(eq(conversations.id, Number(result.insertId)));
  return conversation;
}

export async function deleteConversation(id: number, userId: number) {
  const db = getDb();
  await db
    .delete(conversations)
    .where(and(eq(conversations.id, id), eq(conversations.userId, userId)));
  return { success: true };
}

export async function createMessage(
  conversationId: number,
  role: "user" | "assistant" | "system",
  content: string,
  tokensUsed?: number
) {
  const db = getDb();
  const [result] = await db.insert(messages).values({
    conversationId,
    role,
    content,
    tokensUsed: tokensUsed || 0,
  });
  const [message] = await db
    .select()
    .from(messages)
    .where(eq(messages.id, Number(result.insertId)));
  return message;
}

export async function updateConversationTitle(id: number, userId: number, title: string) {
  const db = getDb();
  await db
    .update(conversations)
    .set({ title })
    .where(and(eq(conversations.id, id), eq(conversations.userId, userId)));
}

export async function findOrCreateChatSettings(userId: number) {
  const db = getDb();
  const [existing] = await db
    .select()
    .from(chatSettings)
    .where(eq(chatSettings.userId, userId));

  if (existing) return existing;

  await db.insert(chatSettings).values({
    userId,
    defaultModel: "anthropic/claude-sonnet-4",
    theme: "auto",
    temperature: "0.70",
  });

  const [settings] = await db
    .select()
    .from(chatSettings)
    .where(eq(chatSettings.userId, userId));
  return settings;
}

export async function updateChatSettings(
  userId: number,
  data: Partial<{
    defaultModel: string;
    theme: "light" | "dark" | "auto";
    temperature: string;
    systemPrompt: string;
  }>
) {
  const db = getDb();
  await db
    .update(chatSettings)
    .set(data)
    .where(eq(chatSettings.userId, userId));

  const [settings] = await db
    .select()
    .from(chatSettings)
    .where(eq(chatSettings.userId, userId));
  return settings;
}
