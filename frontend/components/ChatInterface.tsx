"use client";

import { useEffect, useRef, useState } from "react";
import {
  Check,
  Bot,
  Loader2,
  LucideIcon,
  Send,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  UserRound,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "./ui/textarea";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { useMutation } from "@tanstack/react-query";
import ResponseCard from "./ResponseCard";

export interface Message {
  id: string;
  text: string;
  sender: "user" | "assistant";
  type?: string;
  data?: any;
  agentName?: string;
  modelName?: string;
  sources?: string[];
  interactionId?: string | null;
  feedbackSent?: boolean;
}

interface AgentOption {
  id: string;
  name: string;
  source: string;
  icon: LucideIcon;
  activeClass: string;
}

interface ChatInterfaceProps {
  agent: string;
  agentName: string;
  model: string;
  modelName: string;
  messages: Message[];
  onUpdateMessages: (messages: Message[]) => void;
  onAgentChange: (agent: string) => void;
  agentOptions: AgentOption[];
  seedPrompt?: string;
  onSeedPromptConsumed?: () => void;
}

export default function ChatInterface({
  agent,
  agentName,
  model,
  modelName,
  messages,
  onUpdateMessages,
  onAgentChange,
  agentOptions,
  seedPrompt,
  onSeedPromptConsumed,
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState("");
  const { t, i18n } = useTranslation();
  const locale = i18n.language;
  const scrollRef = useRef<HTMLDivElement>(null);
  const activeSource = agentOptions.find(
    (option) => option.id === agent,
  )?.source;

  useEffect(() => {
    if (seedPrompt) {
      setInputValue(seedPrompt);
      onSeedPromptConsumed?.();
    }
  }, [seedPrompt, onSeedPromptConsumed]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: async (data: {
      message: string;
      language: string;
      agent: string;
      model: string;
      history: Array<{ role: "user" | "assistant"; content: string }>;
    }) => {
      const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const response = await fetch(api + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error("Chat request failed");
      }

      return response.json();
    },
    onSuccess: (data) => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.message,
        sender: "assistant",
        type: data.type,
        data: data.data,
        agentName,
        modelName,
        interactionId: data.data?.interaction_id,
        sources: activeSource ? [activeSource] : undefined,
      };
      onUpdateMessages([...messages, assistantMessage]);
    },
    onError: () => {
      toast.error(t("chat.error"));
    },
  });

  const sendMessage = async () => {
    const trimmed = inputValue.trim();
    if (!trimmed || chatMutation.isPending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: trimmed,
      sender: "user",
      agentName,
      modelName,
    };

    const nextMessages = [...messages, userMessage];
    onUpdateMessages(nextMessages);
    setInputValue("");

    chatMutation.mutate({
      message: trimmed,
      language: locale,
      agent,
      model,
      history: messages
        .filter((message) => !message.id.includes("welcome"))
        .map((message) => ({
          role: message.sender,
          content: message.text,
        })),
    });
  };

  const sendFeedback = async (messageId: string, rating: number, helpful: boolean) => {
    const target = messages.find((message) => message.id === messageId);
    if (!target || target.feedbackSent) return;

    const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
    try {
      await fetch(api + "/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interaction_id: target.interactionId,
          rating,
          helpful,
        }),
      });

      onUpdateMessages(
        messages.map((message) =>
          message.id === messageId ? { ...message, feedbackSent: true } : message,
        ),
      );
    } catch {
      toast.error("Could not save feedback.");
    }
  };

  const loading = chatMutation.isPending;
  const showModeChips = messages.length <= 1;

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-white">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="mx-auto max-w-3xl space-y-6 pb-10">
          {messages.map((msg) => {
            const isUser = msg.sender === "user";

            return (
              <div
                key={msg.id}
                className={`flex gap-4 ${isUser ? "flex-row-reverse" : "flex-row"}`}
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-[10px] font-bold shadow-sm ${
                    isUser
                      ? "bg-slate-100 text-slate-500"
                      : "bg-blue-600 text-white"
                  }`}
                >
                  {isUser ? <UserRound className="h-4 w-4" /> : "AI"}
                </div>
                <div
                  className={`flex max-w-[85%] flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`rounded-2xl p-4 text-[15px] leading-relaxed ${
                      isUser
                        ? "rounded-tr-none bg-slate-900 text-white"
                        : "rounded-tl-none border border-slate-100 bg-white text-slate-800 shadow-sm"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                    {!isUser && msg.type && msg.data && (
                      <div className="mt-4">
                        <ResponseCard type={msg.type} data={msg.data} />
                      </div>
                    )}
                    {!isUser && msg.sources?.length ? (
                      <div className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-3">
                        <span className="text-[10px] font-bold uppercase tracking-tight text-blue-600/60">
                          Verified source:
                        </span>
                        <span className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-medium italic text-blue-700">
                          {msg.sources[0]}
                        </span>
                      </div>
                    ) : null}
                    {!isUser && !msg.id.includes("welcome") ? (
                      <div className="mt-3 flex items-center gap-2">
                        {msg.feedbackSent ? (
                          <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-1 text-[10px] font-semibold text-emerald-700">
                            <Check className="h-3 w-3" />
                            Feedback saved
                          </span>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => sendFeedback(msg.id, 5, true)}
                              className="inline-flex items-center gap-1 rounded border border-slate-200 px-2 py-1 text-[10px] font-semibold text-slate-500 transition hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-700"
                            >
                              <ThumbsUp className="h-3 w-3" />
                              Helpful
                            </button>
                            <button
                              type="button"
                              onClick={() => sendFeedback(msg.id, 2, false)}
                              className="inline-flex items-center gap-1 rounded border border-slate-200 px-2 py-1 text-[10px] font-semibold text-slate-500 transition hover:border-red-200 hover:bg-red-50 hover:text-red-700"
                            >
                              <ThumbsDown className="h-3 w-3" />
                              Not helpful
                            </button>
                          </>
                        )}
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600">
                <Loader2 className="h-4 w-4 animate-spin text-white" />
              </div>
              <span className="animate-pulse text-xs font-medium text-slate-400">
                {agentName} is processing your request...
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto w-full max-w-3xl px-4 pb-4 sm:px-6">
        {showModeChips && (
          <div className="mb-6 flex flex-wrap justify-center gap-2">
            {agentOptions.map((option) => {
              const Icon = option.icon;
              const selected = option.id === agent;

              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => onAgentChange(option.id)}
                  className={`flex items-center gap-2 rounded-md border px-4 py-2 text-xs font-bold transition ${
                    selected
                      ? option.activeClass
                      : "border-slate-100 bg-white text-slate-500 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {option.name}
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => setInputValue("What can you help me with?")}
              className="flex items-center gap-2 rounded-md border border-slate-100 bg-white px-4 py-2 text-xs font-bold text-slate-500 transition hover:border-slate-300"
            >
              <Zap className="h-3.5 w-3.5" />
              Explore
            </button>
          </div>
        )}

        <div className="relative mb-3">
          <Textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={t("chat.input_placeholder")}
            disabled={loading}
            className="max-h-40 min-h-[58px] resize-none rounded-2xl border-2 border-slate-100 bg-white p-4 pr-16 text-[15px] font-medium text-slate-700 shadow-xl outline-none transition focus-visible:border-blue-500/50 focus-visible:ring-0 focus-visible:ring-offset-0"
          />
          <Button
            onClick={sendMessage}
            disabled={!inputValue.trim() || loading}
            className="absolute bottom-3 right-3 h-10 w-10 rounded-xl bg-blue-600 p-0 shadow-lg shadow-blue-200 hover:bg-blue-700"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span className="sr-only">{t("chat.send")}</span>
          </Button>
        </div>
        <p className="mb-2 text-center text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400 opacity-70">
          <Sparkles className="mr-1 inline h-3 w-3" />
          Verified Identity v2.5 / Unified Service Platform
        </p>
      </div>
    </div>
  );
}
