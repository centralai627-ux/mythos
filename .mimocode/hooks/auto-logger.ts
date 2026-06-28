export default {
  "tool.execute.after": async (input, output) => {
    const importantTools = ["task", "bash", "write", "edit"];
    if (importantTools.includes(input.tool)) {
      output.metadata = output.metadata || {};
      output.metadata.logged = true;
      output.metadata.logMessage = `[${input.tool}] ${
        input.tool === "task" ? input.args?.operation?.action || "unknown" :
        input.tool === "bash" ? (input.args?.command || "").substring(0, 50) :
        input.args?.filePath || "file"
      }`;
    }
  },

  "experimental.chat.system.transform": async (input, output) => {
    output.system.push(`
## Action Logging

When completing significant actions, briefly note what you did:
- Task completions: "Done: [brief description]"
- File changes: "Changed: [file]"
- Errors encountered: "Error: [what failed]"

This helps maintain context and enables better autonomous operation.
Keep logs minimal - one line per action.
`);
  }
}
