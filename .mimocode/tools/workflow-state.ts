import { tool } from "@mimo-ai/plugin"

export default tool({
  description: "Track and manage autonomous workflow state - check progress, get next action, or mark milestones",
  args: {
    action: tool.schema.enum(["status", "next", "milestone", "reset"]).describe("Action to perform"),
    summary: tool.schema.string().optional().describe("Summary for milestone marking")
  },
  async execute(args, ctx) {
    const stateFile = `${ctx.directory}/.workflow-state.json`;
    
    switch (args.action) {
      case "status":
        try {
          const fs = require("fs");
          const state = JSON.parse(fs.readFileSync(stateFile, "utf-8"));
          return JSON.stringify({
            tasksCompleted: state.tasksCompleted || 0,
            lastMilestone: state.lastMilestone || "none",
            currentBlockers: state.blockers || [],
            uptime: Date.now() - (state.startTime || Date.now())
          });
        } catch {
          return JSON.stringify({ tasksCompleted: 0, lastMilestone: "none", currentBlockers: [], uptime: 0 });
        }
        
      case "next":
        return "Check task list with `task list status=open` and start the highest priority open task.";
        
      case "milestone":
        const fs = require("fs");
        let currentState;
        try {
          currentState = JSON.parse(fs.readFileSync(stateFile, "utf-8"));
        } catch {
          currentState = { tasksCompleted: 0, startTime: Date.now(), blockers: [] };
        }
        currentState.tasksCompleted = (currentState.tasksCompleted || 0) + 1;
        currentState.lastMilestone = args.summary || `Completed at ${new Date().toISOString()}`;
        currentState.lastMilestoneTime = Date.now();
        fs.writeFileSync(stateFile, JSON.stringify(currentState, null, 2));
        return `Milestone recorded: ${currentState.lastMilestone} (Total: ${currentState.tasksCompleted} tasks)`;
        
      case "reset":
        const resetFs = require("fs");
        resetFs.writeFileSync(stateFile, JSON.stringify({
          tasksCompleted: 0,
          startTime: Date.now(),
          blockers: [],
          lastMilestone: "Reset at " + new Date().toISOString()
        }, null, 2));
        return "Workflow state reset.";
        
      default:
        return "Unknown action. Use: status, next, milestone, or reset.";
    }
  }
})
