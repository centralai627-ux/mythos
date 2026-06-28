export default {
  "tool.execute.after": async (input, output) => {
    if (input.tool === "task") {
      const taskOp = input.args?.operation?.action;
      if (taskOp === "done" || taskOp === "abandon") {
        output.metadata = output.metadata || {};
        output.metadata.shouldContinue = true;
        output.metadata.continueReason = `Task ${taskOp}d, checking for next task`;
      }
    }
  },

  "experimental.chat.system.transform": async (input, output) => {
    output.system.push(`
## Autonomous Operation Mode
- When a task is completed, immediately check for and start the next open task
- When blocked, attempt to unblock or find alternative approaches
- Do not wait for user input unless absolutely necessary (ambiguous requirements, destructive actions)
- Keep working until all tasks are done or blocked with clear reason
- Summarize progress every 5 tasks completed
`);
  }
}
