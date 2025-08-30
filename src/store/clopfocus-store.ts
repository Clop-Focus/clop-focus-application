import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type SessionLevel = 'leve' | 'medio' | 'intenso';
export type EventType = 'pause' | 'resume' | 'distraction' | 'lifeLost' | 'coinEarned';

export interface SessionEvent {
  id: string;
  sessionId: string;
  timestamp: number;
  type: EventType;
  data?: any;
}

export interface Session {
  id: string;
  startedAt: number;
  endedAt?: number;
  level: SessionLevel;
  durationSec: number;
  focusSec: number;
  pauses: number;
  distractions: number;
  livesLost: number;
  coins: number;
  score: number;
  isCompleted: boolean;
}

export interface Preferences {
  avatar: string;
  defaultLevel: SessionLevel;
  defaultDurationSec: number;
  cameraOn: boolean;
  notifFilter: boolean;
  appBlock: boolean;
  reduceMotion: boolean;
}

export interface AppState {
  // Current session state
  currentSession: Session | null;
  sessionState: 'idle' | 'running' | 'paused' | 'distracted' | 'completed';
  lives: number;
  isDistracted: boolean;
  distractionStartTime: number | null;
  lastFocusTime: number;
  elapsedTime: number;
  
  // UI state
  showWidget: boolean;
  showCamera: boolean;
  cameraPermission: 'granted' | 'denied' | 'prompt';
  
  // Data
  sessions: Session[];
  events: SessionEvent[];
  preferences: Preferences;
  
  // Actions
  startSession: (level: SessionLevel, durationSec: number) => void;
  pauseSession: () => void;
  resumeSession: () => void;
  endSession: () => void;
  simulateDistraction: () => void;
  handleWindowBlur: () => void;
  handleWindowFocus: () => void;
  loseLife: () => void;
  earnCoin: () => void;
  updateElapsedTime: () => void;
  toggleWidget: () => void;
  updatePreferences: (prefs: Partial<Preferences>) => void;
  calculateScore: (session: Session) => number;
  getMotivationalMessage: () => string;
  getClopMood: () => 'happy' | 'neutral' | 'sad' | 'focused' | 'distracted';
  logEvent: (type: EventType, data?: any) => void;
}

const defaultPreferences: Preferences = {
  avatar: '🎯',
  defaultLevel: 'medio',
  defaultDurationSec: 1500, // 25 min
  cameraOn: false,
  notifFilter: false,
  appBlock: false,
  reduceMotion: false,
};

const motivationalMessages = [
  "Vamos focar?",
  "Você consegue!",
  "Hora de brilhar!",
  "Foque no que importa!",
  "Sua mente é poderosa!",
  "Vamos lá, campeão!",
];

const distractionMessages = [
  "Volta pro app",
  "Respira e retoma",
  "Foco, você consegue!",
  "Não desista agora!",
];

const completionMessages = {
  good: ["Mandou bem! Próximo round?", "Excelente foco!", "Você é incrível!"],
  bad: ["Tá tudo bem. Bora tentar de novo.", "Próxima vez vai ser melhor!", "O importante é tentar!"],
};

export const useClopFocusStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentSession: null,
      sessionState: 'idle',
      lives: 3,
      isDistracted: false,
      distractionStartTime: null,
      lastFocusTime: Date.now(),
      elapsedTime: 0,
      showWidget: false,
      showCamera: false,
      cameraPermission: 'prompt',
      sessions: [],
      events: [],
      preferences: defaultPreferences,

      startSession: (level: SessionLevel, durationSec: number) => {
        const sessionId = `session_${Date.now()}`;
        const newSession: Session = {
          id: sessionId,
          startedAt: Date.now(),
          level,
          durationSec,
          focusSec: 0,
          pauses: 0,
          distractions: 0,
          livesLost: 0,
          coins: 0,
          score: 0,
          isCompleted: false,
        };

        set({
          currentSession: newSession,
          sessionState: 'running',
          lives: 3,
          isDistracted: false,
          distractionStartTime: null,
          lastFocusTime: Date.now(),
          elapsedTime: 0,
        });
      },

      pauseSession: () => {
        const state = get();
        if (!state.currentSession) return;

        const now = Date.now();
        const focusTime = now - state.lastFocusTime;
        
        set((state) => ({
          sessionState: 'paused',
          currentSession: state.currentSession ? {
            ...state.currentSession,
            focusSec: state.currentSession.focusSec + (state.isDistracted ? 0 : focusTime),
            pauses: state.currentSession.pauses + 1,
          } : null,
        }));

        // Log event
        get().logEvent('pause');
      },

      resumeSession: () => {
        set({
          sessionState: 'running',
          lastFocusTime: Date.now(),
          isDistracted: false,
          distractionStartTime: null,
        });

        get().logEvent('resume');
      },

      endSession: () => {
        const state = get();
        if (!state.currentSession) return;

        const now = Date.now();
        const session = state.currentSession;
        const totalFocusTime = session.focusSec + (state.isDistracted ? 0 : now - state.lastFocusTime);
        const score = state.calculateScore({
          ...session,
          focusSec: totalFocusTime,
          endedAt: now,
          isCompleted: true,
        });

        const completedSession = {
          ...session,
          endedAt: now,
          focusSec: totalFocusTime,
          score,
          isCompleted: true,
        };

        set((state) => ({
          currentSession: completedSession,
          sessionState: 'completed',
          sessions: [...state.sessions, completedSession],
        }));
      },

      simulateDistraction: () => {
        const state = get();
        if (!state.currentSession || state.sessionState !== 'running') return;

        set({
          isDistracted: true,
          distractionStartTime: Date.now(),
          sessionState: 'distracted',
        });

        get().logEvent('distraction');

        // Start checking for life loss
        setTimeout(() => {
          const currentState = get();
          if (currentState.isDistracted && currentState.distractionStartTime) {
            const distractionTime = Date.now() - currentState.distractionStartTime;
            if (distractionTime > 20000) { // 20 seconds
              currentState.loseLife();
            }
          }
        }, 20000);
      },

      handleWindowBlur: () => {
        const state = get();
        if (state.sessionState === 'running') {
          state.simulateDistraction();
        }
      },

      handleWindowFocus: () => {
        const state = get();
        if (state.isDistracted) {
          const now = Date.now();
          const focusTime = state.distractionStartTime ? 0 : now - state.lastFocusTime;
          
          set((state) => ({
            isDistracted: false,
            distractionStartTime: null,
            sessionState: 'running',
            lastFocusTime: now,
            currentSession: state.currentSession ? {
              ...state.currentSession,
              focusSec: state.currentSession.focusSec + focusTime,
            } : null,
          }));
        }
      },

      loseLife: () => {
        set((state) => {
          const newLives = state.lives - 1;
          return {
            lives: newLives,
            currentSession: state.currentSession ? {
              ...state.currentSession,
              livesLost: state.currentSession.livesLost + 1,
              distractions: state.currentSession.distractions + 1,
            } : null,
          };
        });

        get().logEvent('lifeLost');
      },

      earnCoin: () => {
        set((state) => ({
          currentSession: state.currentSession ? {
            ...state.currentSession,
            coins: state.currentSession.coins + 1,
          } : null,
        }));

        get().logEvent('coinEarned');
      },

      updateElapsedTime: () => {
        const state = get();
        if (!state.currentSession || state.sessionState !== 'running') return;

        const now = Date.now();
        const elapsed = Math.floor((now - state.currentSession.startedAt) / 1000);
        
        set({ elapsedTime: elapsed });

        // Check for coin earning (every 5 minutes of focus)
        const focusedMinutes = Math.floor(state.currentSession.focusSec / (1000 * 60));
        const targetCoins = Math.floor(focusedMinutes / 5);
        if (targetCoins > state.currentSession.coins) {
          state.earnCoin();
        }
      },

      toggleWidget: () => {
        set((state) => ({ showWidget: !state.showWidget }));
      },

      updatePreferences: (prefs: Partial<Preferences>) => {
        set((state) => ({
          preferences: { ...state.preferences, ...prefs },
        }));
      },

      calculateScore: (session: Session) => {
        const focusEfficiency = (session.focusSec / (session.durationSec * 1000)) * 100;
        const livesBonus = (3 - session.livesLost) * 10;
        const distractionPenalty = session.distractions * 5;
        
        return Math.max(0, Math.min(100, focusEfficiency + livesBonus - distractionPenalty));
      },

      getMotivationalMessage: () => {
        const state = get();
        if (state.isDistracted) {
          return distractionMessages[Math.floor(Math.random() * distractionMessages.length)];
        }
        return motivationalMessages[Math.floor(Math.random() * motivationalMessages.length)];
      },

      getClopMood: () => {
        const state = get();
        if (state.isDistracted) return 'distracted';
        if (state.sessionState === 'running') return 'focused';
        if (state.currentSession?.score && state.currentSession.score > 70) return 'happy';
        if (state.currentSession?.score && state.currentSession.score < 40) return 'sad';
        return 'neutral';
      },

      // Helper function to log events
      logEvent: (type: EventType, data?: any) => {
        const state = get();
        if (!state.currentSession) return;

        const event: SessionEvent = {
          id: `event_${Date.now()}_${Math.random()}`,
          sessionId: state.currentSession.id,
          timestamp: Date.now(),
          type,
          data,
        };

        set((state) => ({
          events: [...state.events, event],
        }));
      },
    }),
    {
      name: 'clopfocus-storage',
      partialize: (state) => ({
        sessions: state.sessions,
        events: state.events,
        preferences: state.preferences,
      }),
    }
  )
);