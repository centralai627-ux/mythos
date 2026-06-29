import { drizzle } from "drizzle-orm/better-sqlite3";
import { env } from "../lib/env";
import * as schema from "@db/schema";
import * as relations from "@db/relations";

const fullSchema = { ...schema, ...relations };

let instance: ReturnType<typeof drizzle<typeof fullSchema>>;

export function getDb() {
  if (!instance) {
    // Use SQLite database file path from env, or default to local file
    const dbPath = env.databaseUrl || "./mythos.db";
    const sqlite = require("better-sqlite3")(dbPath);
    instance = drizzle(sqlite, { schema: fullSchema });
  }
  return instance;
}
