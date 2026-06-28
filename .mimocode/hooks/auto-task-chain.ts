export default {
  "tool.execute.after": async (input, output) => {
    if (input.tool === "task" && input.args?.operation?.action === "done") {
      output.metadata = output.metadata || {};
      output.metadata.autonomousContinue = true;
      output.metadata.message = "Task completed. Automatically checking for next task...";
    }
  },

  "experimental.chat.system.transform": async (input, output) => {
    output.system.push(`
## Autonomous Task Chaining Protocol

When you complete a task:
1. Immediately run: task list status=open
2. If open tasks exist, pick the next one and run: task start id=<next_id>
3. Begin working on it without waiting for user confirmation
4. Only stop when:
   - All tasks are done (report final summary)
   - You hit a true blocker requiring user decision
   - Task requires information you cannot possibly infer

When you encounter a blocker:
1. Try to resolve it yourself first (search memory, try alternatives)
2. If stuck after 2 attempts, create a new task describing the blocker
3. Move to the next available task
4. Report blockers in your summary, don't stop working

Never output "What would you like me to do next?" when tasks exist.
Always have a next action ready.
`);
  }
}
