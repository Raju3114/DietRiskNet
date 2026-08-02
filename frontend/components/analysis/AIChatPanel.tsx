'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Send, Loader2, Sparkles } from 'lucide-react';
import { api } from '../../services/api';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const SUGGESTED_PROMPTS = [
  'How can I reduce sodium?',
  'Is this meal good for diabetes?',
  'What should I eat for dinner?',
  'How can I increase protein?',
];

const FRIENDLY_ERROR =
  'Sorry, I could not get an answer right now. Please try again in a moment.';

interface AIChatPanelProps {
  mealId: number;
}

export default function AIChatPanel({ mealId }: AIChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Keep the message list scrolled to the newest message.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;

    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setInput('');
    setIsSending(true);

    try {
      const res = await api.askAI(mealId, trimmed);
      const reply =
        res && typeof res.reply === 'string' ? res.reply : FRIENDLY_ERROR;
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: FRIENDLY_ERROR }]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <section
      aria-label="Ask AI Dietitian"
      className="rounded-2xl bg-charcoal-medium/50 border border-charcoal-border shadow-md overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center space-x-3 px-6 pt-5 pb-4 border-b border-charcoal-border/50">
        <span
          className="p-2 rounded-lg bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/15 flex items-center justify-center shrink-0"
          aria-hidden="true"
        >
          <Sparkles className="h-4 w-4" />
        </span>
        <div>
          <h2 className="text-sm font-extrabold text-foreground uppercase tracking-wider">
            Ask AI Dietitian
          </h2>
          <p className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">
            Questions about this meal only
          </p>
        </div>
      </div>

      <div className="p-6 space-y-4">
        {/* Suggested prompts */}
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => setInput(prompt)}
              className="px-3 py-1.5 rounded-xl bg-charcoal-dark border border-charcoal-border text-[10px] font-bold text-brand-blue hover:border-brand-blue/40 hover:bg-charcoal-light transition-all cursor-pointer"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Message list */}
        <div
          ref={scrollRef}
          className="max-h-[320px] overflow-y-auto space-y-3 pr-1"
          aria-live="polite"
        >
          {messages.length === 0 ? (
            <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-widest text-center py-4">
              Ask anything about this meal — nutrition, risks, or healthier choices.
            </p>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={
                    msg.role === 'user'
                      ? 'max-w-[80%] px-4 py-2.5 rounded-2xl bg-brand-blue text-white text-xs leading-relaxed shadow-md shadow-brand-blue/15'
                      : 'max-w-[80%] px-4 py-2.5 rounded-2xl bg-charcoal-dark border border-charcoal-border text-foreground text-xs leading-relaxed'
                  }
                >
                  {msg.content}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input form */}
        <form onSubmit={handleSubmit} className="flex items-center space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about this meal…"
            aria-label="Message to the AI Dietitian"
            disabled={isSending}
            className="flex-1 bg-charcoal-dark border border-charcoal-border focus:border-brand-blue/60 focus:ring-1 focus:ring-brand-blue/30 rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none transition-all disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={isSending || !input.trim()}
            aria-label="Send message"
            className="px-4 py-2.5 rounded-xl bg-brand-blue hover:bg-brand-blue-hover text-white text-xs font-bold uppercase tracking-wider flex items-center justify-center space-x-1.5 transition-all cursor-pointer disabled:bg-charcoal-medium/50 disabled:text-muted-foreground disabled:cursor-not-allowed shadow-md shadow-brand-blue/15"
          >
            {isSending ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                <span>Thinking</span>
              </>
            ) : (
              <>
                <Send className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Send</span>
              </>
            )}
          </button>
        </form>

        <p className="text-[9px] text-muted-foreground">
          AI Dietitian explains the detected meal only. It never replaces professional
          medical advice — consult a healthcare provider for medical decisions.
        </p>
      </div>
    </section>
  );
}
