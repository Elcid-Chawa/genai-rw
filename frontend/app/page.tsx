'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  BookOpen,
  Briefcase,
  Car,
  ChevronRight,
  Compass,
  Languages,
  Leaf,
  Menu,
  MessageSquare,
  PanelRightClose,
  Plus,
  Settings,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useTranslation } from 'react-i18next'
import ChatInterface, { Message } from '../components/ChatInterface'

type AgentId = 'general' | 'business' | 'tourism' | 'insurance' | 'farming'

interface ChatSession {
  id: string
  title: string
  agent: AgentId
  messages: Message[]
  lastUpdated: number
}

const agents = [
  {
    id: 'general',
    name: 'Assistant',
    label: 'Unified Assistant',
    welcome: 'How can I help you today? I am your Rwandan Unified Assistant.',
    source: 'Unified Government Portal',
    description: 'Routes across insurance, tourism, farming, and business.',
    icon: Sparkles,
    accent: 'text-slate-700 bg-slate-50 border-slate-200',
    active: 'bg-slate-900 text-white border-slate-900',
  },
  {
    id: 'business',
    name: 'Business Services',
    label: 'RDB and RRA Desk',
    welcome: 'Welcome to the Business Services desk. How can I help with company registration or investment inquiries today?',
    source: 'RDB Investment Law 2021',
    description: 'Registration, investment, tax, and official business guidance.',
    icon: Briefcase,
    accent: 'text-blue-700 bg-blue-50 border-blue-100',
    active: 'bg-blue-600 text-white border-blue-600',
  },
  {
    id: 'tourism',
    name: 'Tourism Guide',
    label: 'Visit Rwanda Guide',
    welcome: 'Welcome to Visit Rwanda. Ask me about parks, itineraries, budgets, and cultural sites.',
    source: 'Visit Rwanda 2024 guidelines',
    description: 'Itineraries, budgets, and local trip ideas.',
    icon: Compass,
    accent: 'text-emerald-700 bg-emerald-50 border-emerald-100',
    active: 'bg-emerald-600 text-white border-emerald-600',
  },
  {
    id: 'insurance',
    name: 'Insurance Desk',
    label: 'RSSB and Motor Desk',
    welcome: 'Welcome to the Insurance Desk. Ask me about RSSB, Mutuelle, pension schemes, or motor coverage.',
    source: 'RSSB policies and guidelines',
    description: 'Coverage summaries, RSSB guidance, and quote support.',
    icon: Car,
    accent: 'text-cyan-700 bg-cyan-50 border-cyan-100',
    active: 'bg-cyan-600 text-white border-cyan-600',
  },
  {
    id: 'farming',
    name: 'Farming Advisor',
    label: 'Agriculture Desk',
    welcome: 'Welcome to the Farming Advisor. Tell me your crop, district, and season.',
    source: 'Rwanda agriculture guidance',
    description: 'Seasonal crop guidance by district.',
    icon: Leaf,
    accent: 'text-lime-700 bg-lime-50 border-lime-100',
    active: 'bg-lime-600 text-white border-lime-600',
  },
] as const

const models = [
  { id: 'gpt-4o-mini', name: 'GPT-4o mini', note: 'OpenAI, fast everyday assistant' },
  { id: 'gpt-4o', name: 'GPT-4o', note: 'OpenAI, higher reasoning quality' },
  { id: 'gpt-4.1-mini', name: 'GPT-4.1 mini', note: 'OpenAI, balanced long-form tasks' },
  { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', note: 'Google, fast multimodal assistant' },
  { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', note: 'Google, deeper reasoning assistant' },
  { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash Preview', note: 'Google preview model, if enabled for your key' },
]

const starterPrompts = [
  'How do I register a sole proprietorship?',
  'Plan a 1-day tour near Musanze on a 50k RWF budget',
  'Get me a third-party motor quote for a Toyota in Kigali',
  'I grow maize in Nyamagabe; what should I do this month?',
]

function newSession(agent: AgentId = 'general'): ChatSession {
  const config = agents.find((item) => item.id === agent) ?? agents[0]
  return {
    id: Math.random().toString(36).slice(2),
    title: 'New Conversation',
    agent,
    messages: [
      {
        id: `${Date.now()}-welcome`,
        text: config.welcome,
        sender: 'assistant',
        agentName: config.name,
        modelName: 'Gemini 2.5 Flash',
        sources: [config.source],
      },
    ],
    lastUpdated: Date.now(),
  }
}

export default function HomePage() {
  const { t, i18n } = useTranslation()
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash')
  const [seedPrompt, setSeedPrompt] = useState('')
  const [sourcesOpen, setSourcesOpen] = useState(true)
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)

  useEffect(() => {
    const first = newSession('general')
    setSessions([first])
    setCurrentSessionId(first.id)
  }, [])

  const currentSession = useMemo(
    () => sessions.find((session) => session.id === currentSessionId) ?? sessions[0],
    [sessions, currentSessionId],
  )

  const activeAgent = agents.find((agent) => agent.id === currentSession?.agent) ?? agents[0]
  const activeModel = models.find((model) => model.id === selectedModel) ?? models[3]
  const ActiveIcon = activeAgent.icon

  const handleLanguageChange = (newLocale: string) => {
    i18n.changeLanguage(newLocale)
  }

  const handleNewChat = (agent: AgentId = 'general') => {
    const session = newSession(agent)
    setSessions((prev) => [session, ...prev])
    setCurrentSessionId(session.id)
    setMobileSidebarOpen(false)
  }

  const updateMessages = (messages: Message[]) => {
    if (!currentSession) return

    setSessions((prev) =>
      prev.map((session) => {
        if (session.id !== currentSession.id) return session

        const firstUserMessage = messages.find((message) => message.sender === 'user')
        const title =
          session.title === 'New Conversation' && firstUserMessage
            ? `${firstUserMessage.text.slice(0, 34)}${firstUserMessage.text.length > 34 ? '...' : ''}`
            : session.title

        return { ...session, messages, title, lastUpdated: Date.now() }
      }),
    )
  }

  const changeAgent = (agent: AgentId) => {
    if (!currentSession) return
    const config = agents.find((item) => item.id === agent) ?? agents[0]
    setSessions((prev) =>
      prev.map((session) =>
        session.id === currentSession.id
          ? {
              ...session,
              agent,
              messages:
                session.messages.length === 1 && session.messages[0].id.includes('welcome')
                  ? [{
                      ...session.messages[0],
                      text: config.welcome,
                      agentName: config.name,
                      sources: [config.source],
                    }]
                  : session.messages,
            }
          : session,
      ),
    )
  }

  if (!currentSession) {
    return <main className="min-h-screen bg-white" />
  }

  return (
    <main className="flex h-screen overflow-hidden bg-white text-slate-950">
      {mobileSidebarOpen && (
        <button
          type="button"
          aria-label="Close sidebar overlay"
          onClick={() => setMobileSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 transform flex-col bg-slate-950 text-white transition-transform duration-300 lg:relative lg:translate-x-0 ${
          mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4">
          <button
            type="button"
            onClick={() => handleNewChat('general')}
            className="flex w-full items-center gap-3 rounded-md border border-white/10 bg-white/10 px-4 py-3 text-sm font-semibold transition hover:bg-white/15"
          >
            <Plus className="h-4 w-4" />
            New chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-2">
          <p className="px-2 pb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Recent</p>
          <div className="space-y-1">
            {sessions.map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => {
                  setCurrentSessionId(session.id)
                  setMobileSidebarOpen(false)
                }}
                className={`flex w-full items-center gap-3 rounded-md px-3 py-3 text-left text-sm transition ${
                  currentSession.id === session.id
                    ? 'border border-white/10 bg-slate-800 text-white'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-100'
                }`}
              >
                <MessageSquare className="h-4 w-4 shrink-0 opacity-70" />
                <span className="truncate font-medium">{session.title}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="border-t border-slate-800 p-4">
          <button className="flex w-full items-center gap-3 rounded-md p-2 text-sm text-slate-400 transition hover:bg-slate-900 hover:text-white">
            <Settings className="h-4 w-4" />
            Settings
          </button>
          <div className="mt-4 flex items-center gap-3 rounded-md border border-white/5 bg-slate-900 p-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-600 text-xs font-bold">RW</div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-bold">Rwandan User</p>
              <p className="text-[10px] uppercase tracking-wide text-slate-500">Unified Service Platform</p>
            </div>
          </div>
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileSidebarOpen(true)}
              className="rounded-md p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md border ${activeAgent.accent}`}>
              <ActiveIcon className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="truncate text-base font-bold tracking-tight text-slate-800">
                  {currentSession.title}
                </h1>
                <Badge variant="outline" className="hidden rounded-md text-[10px] uppercase tracking-wide sm:inline-flex">
                  {activeAgent.name}
                </Badge>
              </div>
              <p className="truncate text-xs text-slate-500">{activeAgent.label}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger className="h-9 w-[170px] bg-white">
                <SelectValue placeholder="Model" />
              </SelectTrigger>
              <SelectContent>
                {models.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    {model.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={i18n.language} onValueChange={handleLanguageChange}>
              <SelectTrigger className="hidden h-9 w-[132px] bg-white sm:flex">
                <Languages className="mr-2 h-4 w-4 text-slate-500" />
                <SelectValue placeholder="Language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="fr">Francais</SelectItem>
                <SelectItem value="rw">Kinyarwanda</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="icon"
              className="h-9 w-9"
              onClick={() => setSourcesOpen((open) => !open)}
            >
              {sourcesOpen ? <PanelRightClose className="h-4 w-4" /> : <BookOpen className="h-4 w-4" />}
            </Button>
          </div>
        </header>

        <div className="flex min-h-0 flex-1">
          <ChatInterface
            agent={activeAgent.id}
            agentName={activeAgent.name}
            model={selectedModel}
            modelName={activeModel.name}
            messages={currentSession.messages}
            onUpdateMessages={updateMessages}
            onAgentChange={(agent) => changeAgent(agent as AgentId)}
            agentOptions={agents.map((agent) => ({
              id: agent.id,
              name: agent.name,
              source: agent.source,
              icon: agent.icon,
              activeClass: agent.active,
            }))}
            seedPrompt={seedPrompt}
            onSeedPromptConsumed={() => setSeedPrompt('')}
          />

          {sourcesOpen && (
            <aside className="hidden w-80 shrink-0 border-l border-slate-200 bg-white p-5 xl:block">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                <BookOpen className="h-4 w-4" />
                Citations and Sources
              </div>
              <div className={`mt-4 rounded-md border p-4 ${activeAgent.accent}`}>
                <p className="text-[11px] font-bold uppercase tracking-wide opacity-70">Official reference</p>
                <p className="mt-2 text-sm font-bold text-slate-900">{activeAgent.source}</p>
                <p className="mt-1 text-xs text-slate-500">Used as guidance for generated AI answers.</p>
              </div>
              <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4">
                <p className="text-[11px] font-bold uppercase tracking-wide text-slate-400">Model context</p>
                <p className="mt-2 text-sm font-semibold">{activeModel.name}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">{activeModel.note}</p>
              </div>
              <div className="mt-4 grid gap-2">
                {starterPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => setSeedPrompt(prompt)}
                    className="rounded-md border border-slate-200 bg-white p-3 text-left text-xs leading-5 text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
              <div className="mt-auto rounded-md bg-slate-950 p-4 text-white">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-300">
                  <ShieldCheck className="h-4 w-4 text-emerald-300" />
                  Verified official connection
                </div>
              </div>
            </aside>
          )}
        </div>
      </section>
    </main>
  )
}
