import { useState, useRef, useEffect } from "react";
import { MythosLogo, SparkleIcon, SendIcon, BotIcon, UserIcon, PlusIcon, TrashIcon, ChatIcon, MenuIcon, LoadingDots, AttachIcon } from "../components/Icons";
import MarkdownRenderer from "../components/MarkdownRenderer";

interface ToolLog { tool: string; args: any; result: string }
interface Msg { id: number; role: "user" | "assistant"; content: string; attachment?: string; toolLogs?: ToolLog[] }
interface Conv { id: number; title: string; messages: Msg[] }

const MODELS = [
  { id: 'mythos-auto', name: 'Mythos Auto', desc: 'Auto-select best model' },
  { id: 'mythos-code', name: 'Mythos Code', desc: 'Fast coding' },
  { id: 'mythos-code-alt', name: 'Mythos Code Alt', desc: 'Alternative code' },
  { id: 'mythos-ultra', name: 'Mythos Ultra', desc: 'Deep reasoning' },
  { id: 'mythos-vision', name: 'Mythos Vision', desc: 'Image analysis' },
  { id: 'mythos-5', name: 'Mythos-5 (Shannon)', desc: 'Shannon Coder' },
  { id: 'mythos-5-pro', name: 'Mythos-5 Pro', desc: 'Shannon Pro' },
  { id: 'voice-mode', name: '🎤 Voice Mode', desc: 'AI responds with voice only' },
];

export default function ChatSection() {
  const [input, setInput] = useState("");
  const [convs, setConvs] = useState<Conv[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [sidebar, setSidebar] = useState(false);
  const [model, setModel] = useState('mythos-auto');
  const [attachment, setAttachment] = useState<{ name: string; data: string } | null>(null);
  const [audioPlaying, setAudioPlaying] = useState<HTMLAudioElement | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const cur = convs.find((c) => c.id === active);
  const msgs = cur?.messages || [];

  useEffect(() => {
    const chatContainer = endRef.current?.parentElement;
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }, [msgs, loading]);

  const newConv = () => {
    const id = Date.now();
    setConvs((p) => [{ id, title: "New Session", messages: [] }, ...p]);
    setActive(id);
    setAttachment(null);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const delConv = (id: number) => {
    setConvs((p) => p.filter((c) => c.id !== id));
    if (active === id) setActive(null);
  };

  const handleFileAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      const data = ev.target?.result as string;
      setAttachment({ name: file.name, data });
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const removeAttachment = () => setAttachment(null);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && !attachment) || loading) return;
    setLoading(true);
    const text = input.trim();
    setInput("");

    let cid = active;
    if (!cid) {
      cid = Date.now();
      setConvs((p) => [{ id: cid!, title: text.slice(0, 50) || attachment?.name || "New Session", messages: [] }, ...p]);
      setActive(cid);
    }

    let userContent = text;
    if (attachment) {
      userContent = text ? `[File: ${attachment.name}]\n${text}` : `[Attached: ${attachment.name}]`;
    }

    const userMsg: Msg = { id: Date.now(), role: "user", content: userContent, attachment: attachment?.data };
    setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, userMsg], title: c.messages.length === 0 ? (text.slice(0, 50) || attachment?.name || "New Session") : c.title } : c));

    const history = [
      ...(convs.find((c) => c.id === cid)?.messages.map((m) => ({ role: m.role, content: m.content })) || []),
      { role: "user" as const, content: userContent },
    ];

    setAttachment(null);

    try {
      if (window.electronAPI?.chat) {
        const isVoiceMode = model === 'voice-mode';
        const actualModel = isVoiceMode ? 'mythos-auto' : model;
        
        // Add system instruction for voice mode
        const voiceHistory = isVoiceMode 
          ? [{ role: 'system' as const, content: 'You are in Voice Mode. You MUST respond by calling the voice_speak tool to speak your answer aloud. Use this exact format:\n\n```mythos-tool\n{"name": "voice_speak", "args": {"text": "your spoken response here"}}\n```\n\nDo NOT write any other text. ONLY output the mythos-tool block.' }, ...history]
          : history;
        
        const r = await window.electronAPI.chat(voiceHistory, actualModel, attachment?.data || null);
        
        if (isVoiceMode && r.success) {
          // Parse voice_speak tool call from response
          const content = r.content || '';
          const toolMatch = content.match(/```mythos-tool\s*\n([\s\S]*?)\n```/);
          
          if (toolMatch) {
            try {
              const toolCall = JSON.parse(toolMatch[1]);
              if (toolCall.name === 'voice_speak' && toolCall.args?.text) {
                // Execute TTS via IPC
                const ttsResult = await window.electronAPI.voice.speak(toolCall.args.text, toolCall.args.speed || 1.0);
                
                if (ttsResult.success && ttsResult.audioPath) {
                  // Play audio
                  const audio = new Audio(`file://${ttsResult.audioPath}`);
                  setAudioPlaying(audio);
                  audio.play();
                  audio.onended = () => setAudioPlaying(null);
                  
                  // Show spoken text as message
                  const reply: Msg = { 
                    id: Date.now() + 1, 
                    role: "assistant", 
                    content: "🔊 " + toolCall.args.text,
                  };
                  setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, reply] } : c));
                } else {
                  // TTS failed
                  const reply: Msg = { 
                    id: Date.now() + 1, 
                    role: "assistant", 
                    content: "❌ Voice failed: " + (ttsResult.error || "Unknown error"),
                  };
                  setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, reply] } : c));
                }
              } else {
                // Not a voice_speak call
                const reply: Msg = { 
                  id: Date.now() + 1, 
                  role: "assistant", 
                  content: content,
                };
                setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, reply] } : c));
              }
            } catch (parseError) {
              // JSON parse error
              const reply: Msg = { 
                id: Date.now() + 1, 
                role: "assistant", 
                content: content,
              };
              setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, reply] } : c));
            }
          } else {
            // No tool call found - maybe AI wrote text instead
            // Try to speak the text directly
            if (content.length > 10) {
              const ttsResult = await window.electronAPI.voice.speak(content.substring(0, 500), 1.0);
              
              if (ttsResult.success && ttsResult.audioPath) {
                const audio = new Audio(`file://${ttsResult.audioPath}`);
                setAudioPlaying(audio);
                audio.play();
                audio.onended = () => setAudioPlaying(null);
              }
            }
            
            const reply: Msg = { 
              id: Date.now() + 1, 
              role: "assistant", 
              content: "🔊 " + content.substring(0, 150) + (content.length > 150 ? "..." : ""),
            };
            setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, reply] } : c));
          }
        } else {
          // Normal mode
          const reply: Msg = { 
            id: Date.now() + 1, 
            role: "assistant", 
            content: r.success ? (r.content || "No response") : `Error: ${r.error}`,
            toolLogs: r.toolLogs || []
          };
          setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, reply] } : c));
        }
      } else {
        const reply: Msg = { id: Date.now() + 1, role: "assistant", content: "Desktop app is running. Chat will work when connected to API." };
        setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, reply] } : c));
      }
    } catch {
      const reply: Msg = { id: Date.now() + 1, role: "assistant", content: "Connection error. Please try again." };
      setConvs((p) => p.map((c) => c.id === cid ? { ...c, messages: [...c.messages, reply] } : c));
    }
    setLoading(false);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  return (
    <section id="terminal" className="relative min-h-screen py-20" style={{ zIndex: 10 }}>
      <div className="mx-auto w-full max-w-5xl px-4">
        <div className="mb-10 text-center">
          <p className="mb-3 text-xs uppercase tracking-[0.3em]" style={{ color: "rgba(255,215,0,0.6)" }}>Direct Interface</p>
          <h2 className="mb-4 font-light uppercase" style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "clamp(1.5rem,3vw,3rem)", letterSpacing: "-0.02em", color: "#F5F5F5" }}>Agent Terminal</h2>
        </div>
        <div className="flex gap-4 mx-auto" style={{ height: "70vh" }}>
          {/* Sidebar */}
          <div className={`glass-panel flex flex-col overflow-hidden transition-all duration-300 ${sidebar ? "w-64 opacity-100" : "w-0 opacity-0"}`}>
            <div className="flex items-center justify-between border-b border-white/5 p-3">
              <span className="text-[10px] uppercase tracking-[0.15em]" style={{ color: "rgba(245,245,245,0.5)" }}>Sessions</span>
              <button onClick={newConv} className="rounded-full p-1.5 transition-colors hover:bg-white/5"><PlusIcon size={14} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
              {convs.map((c) => (
                <button key={c.id} onClick={() => setActive(c.id)} className={`mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition-all ${active === c.id ? "bg-white/10" : "hover:bg-white/5"}`}>
                  <ChatIcon size={14} />
                  <span className="truncate" style={{ color: active === c.id ? "#F5F5F5" : "rgba(245,245,245,0.5)" }}>{c.title}</span>
                  <button onClick={(ev) => { ev.stopPropagation(); delConv(c.id); }} className="ml-auto rounded p-1 opacity-0 transition-opacity hover:bg-red-500/10 group-hover:opacity-100"><TrashIcon size={12} color="rgba(245,245,245,0.3)" /></button>
                </button>
              ))}
              {convs.length === 0 && <p className="p-3 text-center text-[10px]" style={{ color: "rgba(245,245,245,0.3)" }}>No sessions yet</p>}
            </div>
          </div>
          {/* Main */}
          <div className="glass-panel flex flex-1 flex-col overflow-hidden">
            <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
              <div className="flex items-center gap-3">
                <button onClick={() => setSidebar(!sidebar)} className="rounded-lg p-1.5 transition-colors hover:bg-white/5"><MenuIcon size={16} /></button>
                <div>
                  <h3 className="text-xs font-medium uppercase tracking-[0.1em]" style={{ fontFamily: "'Space Grotesk', sans-serif", color: "#F5F5F5" }}>{cur?.title || "Mythos Agent"}</h3>
                  <p className="text-[10px]" style={{ color: loading ? "rgba(255,215,0,0.6)" : "rgba(245,245,245,0.4)" }}>{loading ? "Thinking..." : "Ready"}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="text-[10px] px-2 py-1 rounded bg-white/5 border border-white/10 outline-none cursor-pointer"
                  style={{ color: "#F5F5F5" }}
                >
                  {MODELS.map(m => (
                    <option key={m.id} value={m.id} style={{ background: "#1a1a2e" }}>{m.name}</option>
                  ))}
                </select>
                <button onClick={newConv} className="rounded-lg p-1.5 transition-colors hover:bg-white/5"><PlusIcon size={16} color="rgba(245,245,245,0.5)" /></button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-thin" style={{ scrollBehavior: 'smooth' }}>
              {msgs.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full animate-pulse-glow" style={{ background: "rgba(255,215,0,0.08)", border: "1px solid rgba(255,215,0,0.2)" }}><SparkleIcon size={28} /></div>
                  <p className="mb-1 text-sm font-medium" style={{ color: "rgba(245,245,245,0.7)" }}>Mythos Agent is ready</p>
                  <p className="max-w-sm text-center text-xs" style={{ color: "rgba(245,245,245,0.4)" }}>Start a conversation. The AI will process your request.</p>
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {msgs.map((m) => (
                    <div key={m.id} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                      {m.role === "assistant" && (
                        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full" style={{ background: "linear-gradient(135deg, #FFD700, #FFA500)", boxShadow: "0 0 15px rgba(255,215,0,0.2)" }}>
                          <MythosLogo size={18} />
                        </div>
                      )}
                      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${m.role === "user" ? "rounded-br-sm" : "rounded-bl-sm"}`} style={{ background: m.role === "user" ? "rgba(255,215,0,0.12)" : "rgba(255,255,255,0.04)", border: m.role === "user" ? "1px solid rgba(255,215,0,0.18)" : "1px solid rgba(255,255,255,0.06)", color: "#F5F5F5" }}>
                        {m.role === "assistant" && (
                          <div className="mb-2 flex items-center gap-2 pb-2" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                            <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "11px", fontWeight: 600, color: "#FFD700", letterSpacing: "0.05em" }}>MYTHOS</span>
                            <span style={{ fontSize: "9px", color: "rgba(245,245,245,0.4)" }}>AI</span>
                          </div>
                        )}
                        {m.attachment && (
                          <div className="mb-2 rounded-lg overflow-hidden border border-white/10">
                            <img src={m.attachment} alt="attachment" className="max-w-full max-h-48 object-contain" />
                          </div>
                        )}
                        {m.toolLogs && m.toolLogs.length > 0 && (
                          <div className="mb-2 space-y-1">
                            {m.toolLogs.map((tl, i) => (
                              <div key={i} className="rounded-lg px-3 py-2 text-[10px]" style={{ background: "rgba(100,220,255,0.08)", border: "1px solid rgba(100,220,255,0.15)" }}>
                                <div className="flex items-center gap-2 mb-1">
                                  <span style={{ color: "#64DCFF", fontWeight: 600 }}>{tl.tool}</span>
                                  <span style={{ color: "rgba(245,245,245,0.4)" }}>{JSON.stringify(tl.args).slice(0, 80)}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        {m.role === "assistant" ? <MarkdownRenderer content={m.content} /> : <span style={{ whiteSpace: 'pre-wrap' }}>{m.content}</span>}
                      </div>
                      {m.role === "user" && <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full" style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.12)" }}><UserIcon size={14} /></div>}
                    </div>
                  ))}
                  {loading && (
                    <div className="flex gap-3">
                      <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full" style={{ background: "linear-gradient(135deg, #FFD700, #FFA500)", boxShadow: "0 0 15px rgba(255,215,0,0.2)" }}>
                        <MythosLogo size={18} />
                      </div>
                      <div className="flex items-center gap-2 rounded-2xl rounded-bl-sm px-4 py-3" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}><LoadingDots /><span className="text-xs" style={{ color: "rgba(245,245,245,0.4)" }}>Mythos is thinking...</span></div>
                    </div>
                  )}
                  <div ref={endRef} />
                </div>
              )}
            </div>
            {/* Attachment Preview */}
            {attachment && (
              <div className="mx-4 mb-2 flex items-center gap-2 rounded-lg p-2" style={{ background: "rgba(255,215,0,0.08)", border: "1px solid rgba(255,215,0,0.15)" }}>
                <div className="h-10 w-10 shrink-0 overflow-hidden rounded">
                  <img src={attachment.data} alt="" className="h-full w-full object-cover" />
                </div>
                <span className="flex-1 truncate text-[10px]" style={{ color: "rgba(245,245,245,0.7)" }}>{attachment.name}</span>
                <button onClick={removeAttachment} className="rounded p-1 hover:bg-white/10" style={{ color: "rgba(245,245,245,0.5)" }}>
                  <TrashIcon size={12} />
                </button>
              </div>
            )}
            {/* Input */}
            <form onSubmit={send} className="border-t border-white/5 px-4 py-3">
              <div className="flex items-center gap-3">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,.pdf,.txt,.md,.csv,.json,.xml,.html,.css,.js,.ts,.py,.java,.cpp,.c,.rs,.go"
                  onChange={handleFileAttach}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all hover:scale-105"
                  style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)" }}
                  title="Attach file"
                >
                  <AttachIcon size={16} color="rgba(245,245,245,0.5)" />
                </button>
                <input ref={inputRef} type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask Mythos anything..." className="glass-input flex-1 px-5 py-3 text-xs" disabled={loading} />
                <button type="submit" disabled={loading || (!input.trim() && !attachment)} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all hover:scale-105 disabled:opacity-30" style={{ background: "linear-gradient(135deg,#FFD700,#FFC107)", color: "#1A1A1A" }}><SendIcon size={16} color="#1A1A1A" /></button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}
