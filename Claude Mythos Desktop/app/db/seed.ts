import { getDb } from "../api/queries/connection";
import { users, conversations, messages, chatSettings } from "./schema";

async function seed() {
  const db = getDb();
  console.log("Seeding database...");

  // Insert sample user
  const userId = await db.insert(users).values({
    unionId: "sample-user-001",
    name: "Sample User",
    email: "user@mythos.local",
    role: "admin",
  }).returning().get();

  console.log(`Created user: ${userId.id}`);

  // Insert sample conversation
  const convId = await db.insert(conversations).values({
    userId: userId.id,
    title: "Welcome to Mythos",
    model: "anthropic/claude-sonnet-4",
  }).returning().get();

  console.log(`Created conversation: ${convId.id}`);

  // Insert sample message
  await db.insert(messages).values({
    conversationId: convId.id,
    role: "assistant",
    content: "Welcome to Mythos Desktop! I'm your AI assistant.",
    tokensUsed: 50,
  });

  console.log("Done seeding.");
  process.exit(0);
}

seed();
