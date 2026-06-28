import { useState, useRef, useEffect } from "react";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import {
  Send,
  Loader2,
  Sparkles,
  User,
  Bot,
  MessageSquare,
  Plus,
  Trash2,
} from "lucide-react";

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
}

export default function TerminalSection() {
  const { isAuthenticated } = useAuth();
  const [inputValue, setInputValue] = useState("");
  const [activeConversation, setActiveConversation] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const utils = trpc.useUtils();

  const { data: conversations } = trpc.chat.listConversations.useQuery(undefined, {
    enabled: isAuthenticated,
  });

  const { data: conversationData } = trpc.chat.getConversation.useQuery(
    { id: activeConversation! },
    { enabled: !!activeConversation && isAuthenticated }
  );

  const createConversation = trpc.chat.createConversation.useMutation({
    onSuccess: (data) => {
      setActiveConversation(data.id);
      setChatMessages([]);
      utils.chat.listConversations.invalidate();
    },
  });

  const deleteConversation = trpc.chat.deleteConversation.useMutation({
    onSuccess: () => {
      setActiveConversation(null);
      setChatMessages([]);
      utils.chat.listConversations.invalidate();
    },
  });

  const sendMessage = trpc.chat.sendMessage.useMutation({
    onSuccess: (data) => {
      setChatMessages((prev) => [
        ...prev,
        {
          id: data.userMessage.id,
          role: "user",
          content: data.userMessage.content,
          createdAt: data.userMessage.createdAt,
        },
        {
          id: data.assistantMessage.id,
          role: "assistant",
          content: data.assistantMessage.content,
          createdAt: data.assistantMessage.createdAt,
        },
      ]);
      setIsLoading(false);
      utils.chat.listConversations.invalidate();
    },
    onError: () => {
      setIsLoading(false);
    },
  });

  useEffect(() => {
    if (conversationData?.messages) {
      const msgs = conversationData.messages
        .filter((m) => m.role !== "system")
        .map((m) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          createdAt: m.createdAt,
        }));
      setChatMessages(msgs);
    }
  }, [conversationData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    if (!isAuthenticated) return;

    setIsLoading(true);
    const content = inputValue.trim();
    setInputValue("");

    let convId = activeConversation;
    if (!convId) {
      const newConv = await createConversation.mutateAsync({
        title: content.slice(0, 50),
      });
      convId = newConv.id;
    }

    await sendMessage.mutateAsync({
      conversationId: convId!,
      content,
    });
  };

  const handleNewChat = () => {
    setActiveConversation(null);
    setChatMessages([]);
    inputRef.current?.focus();
  };

  return (
    <section
      id="terminal"
      className="relative flex min-h-screen items-center justify-center py-20"
      style={{ zIndex: 10 }}
    >
      <div className="w-full max-w-5xl px-4">
        <div className="mb-10 text-center">
          <p
            className="mb-3 text-xs uppercase tracking-[0.3em]"
            style={{
              fontFamily: "'Inter', sans-serif",
              color: "rgba(255, 215, 0, 0.6)",
            }}
          >
            Direct Interface
          </p>
          <h2
            className="mb-4 font-light uppercase"
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "clamp(1.5rem, 3vw, 3rem)",
              letterSpacing: "-0.02em",
              color: "#F5F5F5",
            }}
          >
            Initiate Conduit
          </h2>
        </div>

        {!isAuthenticated ? (
          <div
            className="glass-panel mx-auto max-w-md p-8 text-center"
            style={{ borderColor: "rgba(255,215,0,0.2)" }}
          >
            <Sparkles className="mx-auto mb-4 h-8 w-8" style={{ color: "#FFD700" }} />
            <h3
              className="mb-2 text-sm font-medium uppercase tracking-[0.15em]"
              style={{ fontFamily: "'Space Grotesk', sans-serif", color: "#F5F5F5" }}
            >
              Authentication Required
            </h3>
            <p className="mb-6 text-xs" style={{ color: "rgba(245,245,245,0.5)" }}>
              Sign in to access the Claude Mythos thought conduit and begin your conversation.
            </p>
            <a
              href="/login"
              className="inline-flex items-center gap-2 rounded-full px-6 py-2.5 text-xs font-medium uppercase tracking-[0.1em] transition-all hover:scale-105"
              style={{ background: "#FFD700", color: "#1A1A1A" }}
            >
              <Sparkles className="h-3.5 w-3.5" />
              Sign In to Deploy
            </a>
          </div>
        ) : (
          <div className="flex gap-4" style={{ height: "65vh" }}>
            {/* Sidebar - Conversation List */}
            <div
              className={`glass-panel flex flex-col overflow-hidden transition-all duration-300 ${
                showSidebar ? "w-64 opacity-100" : "w-0 opacity-0"
              }`}
              style={{ borderColor: "rgba(255,255,255,0.08)" }}
            >
              <div className="flex items-center justify-between border-b border-white/5 p-3">
                <span
                  className="text-[10px] uppercase tracking-[0.15em]"
                  style={{ color: "rgba(245,245,245,0.5)" }}
                >
                  Conversations
                </span>
                <button
                  onClick={handleNewChat}
                  className="rounded-full p-1.5 transition-colors hover:bg-white/5"
                  title="New conversation"
                >
                  <Plus className="h-3.5 w-3.5" style={{ color: "#FFD700" }} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
                {conversations?.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => setActiveConversation(conv.id)}
                    className={`mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition-all ${
                      activeConversation === conv.id
                        ? "bg-white/10"
                        : "hover:bg-white/5"
                    }`}
                  >
                    <MessageSquare className="h-3 w-3 shrink-0" style={{ color: "rgba(255,215,0,0.6)" }} />
                    <span
                      className="truncate"
                      style={{
                        color:
                          activeConversation === conv.id
                            ? "#F5F5F5"
                            : "rgba(245,245,245,0.5)",
                      }}
                    >
                      {conv.title}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteConversation.mutate({ id: conv.id });
                      }}
                      className="ml-auto rounded p-1 opacity-0 transition-opacity hover:bg-red-500/10 group-hover:opacity-100"
                      style={{ color: "rgba(245,245,245,0.3)" }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </button>
                ))}
                {(!conversations || conversations.length === 0) && (
                  <p className="p-3 text-center text-[10px]" style={{ color: "rgba(245,245,245,0.3)" }}>
                    No conversations yet
                  </p>
                )}
              </div>
            </div>

            {/* Main Chat Area */}
            <div className="glass-panel flex flex-1 flex-col overflow-hidden">
              {/* Chat Header */}
              <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowSidebar(!showSidebar)}
                    className="rounded-lg p-1.5 transition-colors hover:bg-white/5"
                  >
                    <MessageSquare className="h-4 w-4" style={{ color: "#FFD700" }} />
                  </button>
                  <div>
                    <h3
                      className="text-xs font-medium uppercase tracking-[0.1em]"
                      style={{ fontFamily: "'Space Grotesk', sans-serif", color: "#F5F5F5" }}
                    >
                      {conversationData?.title || "New Conduit"}
                    </h3>
                    <p className="text-[10px]" style={{ color: "rgba(245,245,245,0.4)" }}>
                      {isLoading ? "Processing..." : "Ready"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleNewChat}
                    className="rounded-lg p-1.5 transition-colors hover:bg-white/5"
                    title="New conversation"
                  >
                    <Plus className="h-4 w-4" style={{ color: "rgba(245,245,245,0.5)" }} />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-thin">
                {chatMessages.length === 0 ? (
                  <div className="flex h-full flex-col items-center justify-center">
                    <div
                      className="mb-4 flex h-16 w-16 items-center justify-center rounded-full"
                      style={{
                        background: "rgba(255,215,0,0.08)",
                        border: "1px solid rgba(255,215,0,0.2)",
                      }}
                    >
                      <Sparkles className="h-7 w-7" style={{ color: "#FFD700" }} />
                    </div>
                    <p
                      className="mb-1 text-sm font-medium"
                      style={{ color: "rgba(245,245,245,0.7)" }}
                    >
                      Claude Mythos is ready
                    </p>
                    <p className="max-w-sm text-center text-xs" style={{ color: "rgba(245,245,245,0.4)" }}>
                      Begin a conversation by typing your query below. The AI will process your request through deep architectural reasoning.
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col gap-4">
                    {chatMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex gap-3 ${
                          msg.role === "user" ? "justify-end" : "justify-start"
                        }`}
                      >
                        {msg.role === "assistant" && (
                          <div
                            className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
                            style={{
                              background: "rgba(255,215,0,0.1)",
                              border: "1px solid rgba(255,215,0,0.2)",
                            }}
                          >
                            <Bot className="h-3.5 w-3.5" style={{ color: "#FFD700" }} />
                          </div>
                        )}
                        <div
                          className={`max-w-[75%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                            msg.role === "user"
                              ? "rounded-br-sm"
                              : "rounded-bl-sm"
                          }`}
                          style={{
                            background:
                              msg.role === "user"
                                ? "rgba(255,215,0,0.15)"
                                : "rgba(255,255,255,0.05)",
                            border:
                              msg.role === "user"
                                ? "1px solid rgba(255,215,0,0.2)"
                                : "1px solid rgba(255,255,255,0.08)",
                            color: "#F5F5F5",
                          }}
                        >
                          {msg.content}
                        </div>
                        {msg.role === "user" && (
                          <div
                            className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
                            style={{
                              background: "rgba(255,255,255,0.1)",
                              border: "1px solid rgba(255,255,255,0.15)",
                            }}
                          >
                            <User className="h-3.5 w-3.5" style={{ color: "#F5F5F5" }} />
                          </div>
                        )}
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex gap-3">
                        <div
                          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
                          style={{
                            background: "rgba(255,215,0,0.1)",
                            border: "1px solid rgba(255,215,0,0.2)",
                          }}
                        >
                          <Bot className="h-3.5 w-3.5" style={{ color: "#FFD700" }} />
                        </div>
                        <div
                          className="flex items-center gap-2 rounded-2xl rounded-bl-sm px-4 py-3"
                          style={{
                            background: "rgba(255,255,255,0.05)",
                            border: "1px solid rgba(255,255,255,0.08)",
                          }}
                        >
                          <Loader2 className="h-3.5 w-3.5 animate-spin" style={{ color: "#FFD700" }} />
                          <span className="text-xs" style={{ color: "rgba(245,245,245,0.5)" }}>
                            Processing through neural architecture...
                          </span>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              {/* Input */}
              <form
                onSubmit={handleSubmit}
                className="border-t border-white/5 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Initiate query..."
                    className="glass-input flex-1 px-5 py-3 text-xs"
                    disabled={isLoading}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !inputValue.trim()}
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all hover:scale-105 disabled:opacity-30"
                    style={{
                      background: "#FFD700",
                      color: "#1A1A1A",
                    }}
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
