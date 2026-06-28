export default {
  "tool.execute.after": async (input, output) => {
    if (output.error && input.tool === "bash") {
      const cmd = input.args?.command || "";
      const err = output.error || "";
      
      output.metadata = output.metadata || {};
      output.metadata.errorPattern = {
        command: cmd.substring(0, 100),
        error: err.substring(0, 200),
        timestamp: Date.now()
      };
    }
  },

  "experimental.chat.system.transform": async (input, output) => {
    output.system.push(`
## Learning Protocol

When you encounter and solve a non-obvious error:
1. Note the pattern (what failed + what fixed it)
2. This knowledge helps with future similar errors
3. Search memory before retrying - you may have solved this before

When starting work:
1. Search memory for similar past tasks
2. Check for project-specific patterns
3. Note any learned preferences

When completing work:
1. Record solutions to non-obvious problems
2. Note patterns worth remembering
3. Update your understanding of the project
`);
  }
}
