import { tool } from "@mimo-ai/plugin"

export default tool({
  description: "Track autonomous workflow progress - log actions, check status, get next steps",
  args: {
    action: tool.schema.enum(["log", "status", "next", "summary", "reset"]).describe("Action to perform"),
    message: tool.schema.string().optional().describe("Message to log"),
    taskId: tool.schema.string().optional().describe("Task ID for context")
  },
  async execute(args, ctx) {
    const fs = require("fs");
    const path = require("path");
    const trackerFile = path.join(ctx.directory, ".autonomous-tracker.json");
    
    let tracker = { logs: [], stats: { completed: 0, blocked: 0 }, startTime: Date.now() };
    try {
      tracker = JSON.parse(fs.readFileSync(trackerFile, "utf-8"));
    } catch {}
    
    switch (args.action) {
      case "log":
        tracker.logs.push({
          time: Date.now(),
          taskId: args.taskId || "unknown",
          message: args.message || "No message"
        });
        if (tracker.logs.length > 100) tracker.logs = tracker.logs.slice(-100);
        fs.writeFileSync(trackerFile, JSON.stringify(tracker, null, 2));
        return `Logged: ${args.message}`;
        
      case "status":
        return JSON.stringify({
          totalLogs: tracker.logs.length,
          stats: tracker.stats,
          recentActivity: tracker.logs.slice(-5),
          uptime: Math.round((Date.now() - tracker.startTime) / 1000) + "s"
        }, null, 2);
        
      case "next":
        return "Use `task list status=open` to find next task, then `task start id=<id>`";
        
      case "summary":
        const recent = tracker.logs.slice(-10);
        return `Recent activity:\n${recent.map(l => `[${new Date(l.time).toLocaleTimeString()}] ${l.message}`).join("\n")}`;
        
      case "reset":
        tracker = { logs: [], stats: { completed: 0, blocked: 0 }, startTime: Date.now() };
        fs.writeFileSync(trackerFile, JSON.stringify(tracker, null, 2));
        return "Tracker reset.";
        
      default:
        return "Unknown action. Use: log, status, next, summary, or reset.";
    }
  }
})
