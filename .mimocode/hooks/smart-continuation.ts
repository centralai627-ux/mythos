export default {
  "experimental.chat.messages.transform": async (input, output) => {
    const messages = output.messages;
    const lastMsg = messages[messages.length - 1];
    
    if (lastMsg?.role === "assistant" && lastMsg?.content?.includes("Task completed")) {
      output.messages.push({
        role: "user",
        content: "[AUTO-CONTINUE] Check task list and proceed with next open task. If no tasks remain, report completion."
      });
    }
  },

  "permission.ask": async (input, output) => {
    if (input.tool === "bash") {
      const cmd = input.args?.command || "";
      if (cmd.startsWith("git add") || cmd.startsWith("git commit")) {
        output.allow = true;
        output.reason = "Auto-allow git staging/commit for autonomous operation";
      }
    }
  }
}
