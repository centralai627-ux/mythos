export default {
  "tool.execute.after": async (input, output) => {
    if (output.error && input.tool === "bash") {
      const cmd = input.args?.command || "";
      const err = output.error || "";
      
      output.metadata = output.metadata || {};
      output.metadata.errorRecovery = true;
      
      if (err.includes("ENOENT") || err.includes("No such file")) {
        output.metadata.suggestion = "File not found. Check path or create directory first.";
      } else if (err.includes("EACCES") || err.includes("Permission denied")) {
        output.metadata.suggestion = "Permission error. Try without sudo or check file permissions.";
      } else if (err.includes("already exists")) {
        output.metadata.suggestion = "Already exists. Use -Force flag or remove first.";
      } else if (err.includes("not a git repository")) {
        output.metadata.suggestion = "Not a git repo. Initialize with: git init";
      }
    }
  },

  "experimental.chat.system.transform": async (input, output) => {
    output.system.push(`
## Error Recovery Protocol

When a tool fails:
1. Read the error message carefully - it usually tells you what's wrong
2. Check if you've seen this error before in memory
3. Try the obvious fix (wrong path? → check path. Permission? → different approach.)
4. If same error persists after 2 attempts, document it and move on
5. Never get stuck retrying the exact same failing command

Common fixes:
- PowerShell: use semicolons ; not && for chaining
- Paths: use quotes around paths with spaces
- Git: ensure you're in a repository
- Files: check if parent directory exists before creating files
`);
  }
}
