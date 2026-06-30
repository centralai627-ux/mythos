import { drizzle } from "drizzle-orm/sql-js";
import { env } from "../lib/env";
import * as schema from "@db/schema";
import * as relations from "@db/relations";

const fullSchema = { ...schema, ...relations };

let instance: ReturnType<typeof drizzle<typeof fullSchema>>;

export async function getDb() {
  if (!instance) {
    // Use sql-js (pure JavaScript, no native compilation needed)
    const initSqlJs = require("sql.js");
    const SQL = await initSqlJs();
    
    // Load database from file if exists, or create new
    const fs = require("fs");
    const dbPath = env.databaseUrl || "./mythos.db";
    
    let db;
    if (fs.existsSync(dbPath)) {
      const buffer = fs.readFileSync(dbPath);
      db = new SQL.Database(buffer);
    } else {
      db = new SQL.Database();
    }
    
    instance = drizzle(db, { schema: fullSchema });
  }
  return instance;
}
