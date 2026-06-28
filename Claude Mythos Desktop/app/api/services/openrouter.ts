const OPENROUTER_API_KEY = "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";
const OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1";

interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

interface OpenRouterResponse {
  choices: Array<{
    message: {
      content: string;
      role: string;
    };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  error?: {
    message: string;
    code: number;
  };
}

export async function sendChatMessage(
  messages: ChatMessage[],
  model: string = "anthropic/claude-sonnet-4",
  temperature: number = 0.7,
  systemPrompt?: string | null
): Promise<{ content: string; tokensUsed: number }> {
  const formattedMessages: ChatMessage[] = [];

  if (systemPrompt) {
    formattedMessages.push({ role: "system", content: systemPrompt });
  }

  formattedMessages.push(...messages);

  const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${OPENROUTER_API_KEY}`,
      "HTTP-Referer": "https://claude-mythos.ai",
      "X-Title": "Claude Mythos",
    },
    body: JSON.stringify({
      model,
      messages: formattedMessages,
      temperature,
      max_tokens: 4096,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`OpenRouter API error (${response.status}): ${errorText}`);
  }

  const data = (await response.json()) as OpenRouterResponse;

  if (data.error) {
    throw new Error(`OpenRouter error: ${data.error.message}`);
  }

  const content = data.choices[0]?.message?.content || "";
  const tokensUsed = data.usage?.total_tokens || 0;

  return { content, tokensUsed };
}

export async function pollForCompletion(
  messages: ChatMessage[],
  model: string = "anthropic/claude-sonnet-4",
  temperature: number = 0.7,
  systemPrompt?: string | null,
  maxWaitMs: number = 60000,
  pollIntervalMs: number = 500
): Promise<{ content: string; tokensUsed: number }> {
  const startTime = Date.now();

  while (Date.now() - startTime < maxWaitMs) {
    try {
      const result = await sendChatMessage(messages, model, temperature, systemPrompt);
      return result;
    } catch (error) {
      const elapsed = Date.now() - startTime;
      if (elapsed >= maxWaitMs) {
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    }
  }

  throw new Error("OpenRouter polling timeout");
}
