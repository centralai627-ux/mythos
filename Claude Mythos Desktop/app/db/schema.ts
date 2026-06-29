import {
  sqliteTable,
  text,
  integer,
  real,
} from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  unionId: text("unionId").notNull().unique(),
  name: text("name"),
  email: text("email"),
  avatar: text("avatar"),
  role: text("role", { enum: ["user", "admin"] }).default("user").notNull(),
  createdAt: integer("createdAt", { mode: "timestamp" }).default(new Date()).notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).default(new Date()).notNull(),
  lastSignInAt: integer("lastSignInAt", { mode: "timestamp" }).default(new Date()).notNull(),
});

export const conversations = sqliteTable("conversations", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  userId: integer("userId")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  title: text("title").notNull().default("New Conversation"),
  model: text("model").notNull().default("anthropic/claude-sonnet-4"),
  createdAt: integer("createdAt", { mode: "timestamp" }).default(new Date()).notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).default(new Date()).notNull(),
});

export const messages = sqliteTable("messages", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  conversationId: integer("conversationId")
    .notNull()
    .references(() => conversations.id, { onDelete: "cascade" }),
  role: text("role", { enum: ["user", "assistant", "system"] }).notNull(),
  content: text("content").notNull(),
  tokensUsed: integer("tokensUsed").default(0),
  createdAt: integer("createdAt", { mode: "timestamp" }).default(new Date()).notNull(),
});

export const chatSettings = sqliteTable("chat_settings", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  userId: integer("userId")
    .notNull()
    .unique()
    .references(() => users.id, { onDelete: "cascade" }),
  defaultModel: text("defaultModel")
    .notNull()
    .default("anthropic/claude-sonnet-4"),
  theme: text("theme", { enum: ["light", "dark", "auto"] }).default("auto").notNull(),
  temperature: real("temperature").default(0.70),
  systemPrompt: text("systemPrompt"),
  createdAt: integer("createdAt", { mode: "timestamp" }).default(new Date()).notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).default(new Date()).notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;
export type Conversation = typeof conversations.$inferSelect;
export type Message = typeof messages.$inferSelect;
export type ChatSettings = typeof chatSettings.$inferSelect;
