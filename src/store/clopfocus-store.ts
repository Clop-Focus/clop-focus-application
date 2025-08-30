import { create } from 'zustand'

export type SessionLevel = 'leve' | 'medio' | 'intenso'
export type SessionState = 'running' | 'paused' | 'idle'

type Preferences = {
  defaultLevel: SessionLevel
  defaultDurationSec: number
  cameraOn: boolean
}

type CurrentSession = {
  level: SessionLevel
  durationSec: number
  focusSec: number
  coins: number
  pauses: number
  distractions: number
  isCompleted?: boolean
  livesLost?: number
} | null

type ClopState = {
  preferences: Preferences
  currentSession: CurrentSession
  sessionState: SessionState
  lives: number
  isDistracted: boolean
  elapsedTime: number
  showWidget: boolean

  // ações
  startSession: (level: SessionLevel, durationSec: number) => void
  pauseSession: () => void
  resumeSession: () => void
  endSession: () => void
  simulateDistraction: () => void
  updateElapsedTime: () => void
  toggleWidget: () => void
  handleWindowBlur: () => void
  handleWindowFocus: () => void
  updatePreferences: (p: Partial<Preferences>) => void
  calculateScore: (session: NonNullable<CurrentSession>) => number

  // (opcionais legados)
  showCamera?: boolean
}

export const useClopFocusStore = create<ClopState>()((set, get) => ({
  preferences: {
    defaultLevel: 'medio',
    defaultDurationSec: 1500,
    cameraOn: false,
  },
  currentSession: null,
  sessionState: 'idle',
  lives: 3,
  isDistracted: false,
  elapsedTime: 0,
  showWidget: false,

  startSession: (level, durationSec) => {
    const d = durationSec || get().preferences.defaultDurationSec
    set({
      currentSession: {
        level,
        durationSec: d,
        focusSec: 0,
        coins: 0,
        pauses: 0,
        distractions: 0,
        isCompleted: false,
        livesLost: 0,
      },
      sessionState: 'running',
      elapsedTime: 0,
    })
  },
  pauseSession: () => set((s) => ({ sessionState: 'paused', currentSession: s.currentSession && { ...s.currentSession, pauses: s.currentSession.pauses + 1 } })),
  resumeSession: () => set({ sessionState: 'running' }),
  endSession: () => {
    const { currentSession, elapsedTime } = get()
    if (currentSession) {
      // Marca a sessão como completada antes de limpar
      const completedSession = {
        ...currentSession,
        focusSec: elapsedTime * 1000,
        isCompleted: true,
        livesLost: 3 - get().lives,
      }
      // Aqui você poderia salvar a sessão em um histórico se quiser
      set({ currentSession: completedSession, sessionState: 'idle' })
    } else {
      set({ currentSession: null, sessionState: 'idle', elapsedTime: 0 })
    }
  },
  simulateDistraction: () => set((s) => ({ 
    isDistracted: true, 
    lives: Math.max(0, s.lives - 1),
    currentSession: s.currentSession && { ...s.currentSession, distractions: s.currentSession.distractions + 1 } 
  })),
  updateElapsedTime: () => {
    const { sessionState, elapsedTime, currentSession } = get()
    if (sessionState !== 'running' || !currentSession) return
    const next = elapsedTime + 1
    set({
      elapsedTime: next,
      currentSession: { ...currentSession, focusSec: next * 1000 },
      isDistracted: false,
    })
  },
  toggleWidget: () => set((s) => ({ showWidget: !s.showWidget })),
  handleWindowBlur: () => {},    // mantenha conforme seu app
  handleWindowFocus: () => {},   // idem
  updatePreferences: (p) => set((s) => ({ preferences: { ...s.preferences, ...p } })),
  calculateScore: (session) => {
    const focusEfficiency = (session.focusSec / (session.durationSec * 1000)) * 100
    const distractionPenalty = session.distractions * 10
    const pausePenalty = session.pauses * 5
    const livesBonus = (3 - (session.livesLost || 0)) * 15
    
    let score = Math.round(focusEfficiency - distractionPenalty - pausePenalty + livesBonus)
    return Math.max(0, Math.min(100, score))
  },
}))