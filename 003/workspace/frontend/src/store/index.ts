import { create } from 'zustand';
import type { User, Conversation, Message, ModelInfo } from '../types';

// --- Auth Store ---
interface AuthState {
  user: User | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  guestId: string;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
  initGuest: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoggedIn: false,
  isLoading: true,
  guestId: '',

  setUser: (user) => set({ user, isLoggedIn: !!user }),
  setLoading: (loading) => set({ isLoading: loading }),

  logout: () => {
    set({ user: null, isLoggedIn: false });
    // Guest mode after logout
    const guestId = localStorage.getItem('guest_id');
    if (!guestId) {
      const newId = 'g_' + Math.random().toString(36).substring(2, 18);
      localStorage.setItem('guest_id', newId);
      set({ guestId: newId });
    } else {
      set({ guestId });
    }
  },

  initGuest: () => {
    let guestId = localStorage.getItem('guest_id');
    if (!guestId) {
      guestId = 'g_' + Math.random().toString(36).substring(2, 18);
      localStorage.setItem('guest_id', guestId);
    }
    set({ guestId, isLoading: false });
  },

  fetchMe: async () => {
    try {
      set({ isLoading: true });
      const resp = await fetch('/api/auth/me', { credentials: 'include' });
      if (resp.ok) {
        const user = await resp.json();
        set({ user, isLoggedIn: true, isLoading: false });
      } else {
        get().initGuest();
      }
    } catch {
      get().initGuest();
    }
  },
}));

// --- UI Store ---
interface UIState {
  sidebarOpen: boolean;
  mode: 'chat' | 'voice';
  currentConversationId: string | null;
  toastMessage: string | null;
  toastType: 'success' | 'error' | 'info';
  showSettingsModal: boolean;
  showModelSelector: boolean;
  showMergeDialog: boolean;
  searchQuery: string;

  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setMode: (mode: 'chat' | 'voice') => void;
  setCurrentConversationId: (id: string | null) => void;
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
  hideToast: () => void;
  setShowSettingsModal: (show: boolean) => void;
  setShowModelSelector: (show: boolean) => void;
  setShowMergeDialog: (show: boolean) => void;
  setSearchQuery: (q: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  mode: 'chat',
  currentConversationId: null,
  toastMessage: null,
  toastType: 'info',
  showSettingsModal: false,
  showModelSelector: false,
  showMergeDialog: false,
  searchQuery: '',

  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setMode: (mode) => set({ mode }),
  setCurrentConversationId: (id) => set({ currentConversationId: id }),
  showToast: (message, type = 'info') => {
    set({ toastMessage: message, toastType: type });
    setTimeout(() => set({ toastMessage: null }), 3000);
  },
  hideToast: () => set({ toastMessage: null }),
  setShowSettingsModal: (show) => set({ showSettingsModal: show }),
  setShowModelSelector: (show) => set({ showModelSelector: show }),
  setShowMergeDialog: (show) => set({ showMergeDialog: show }),
  setSearchQuery: (q) => set({ searchQuery: q }),
}));

// --- Model Store ---
interface ModelState {
  models: ModelInfo[];
  selectedModelId: string;
  isLoading: boolean;
  fetchModels: () => Promise<void>;
  setSelectedModel: (id: string) => void;
  getSelectedModel: () => ModelInfo | undefined;
}

export const useModelStore = create<ModelState>((set, get) => ({
  models: [],
  selectedModelId: 'openrouter/auto',
  isLoading: false,

  fetchModels: async () => {
    set({ isLoading: true });
    try {
      const resp = await fetch('/api/models');
      const data = await resp.json();
      set({ models: data.models || [], isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },
  setSelectedModel: (id) => set({ selectedModelId: id }),
  getSelectedModel: () => {
    const { models, selectedModelId } = get();
    return models.find((m) => m.id === selectedModelId);
  },
}));

// --- Conversation Store ---
interface ConversationState {
  conversations: Conversation[];
  currentMessages: Message[];
  isLoadingConversations: boolean;
  isLoadingMessages: boolean;
  isStreaming: boolean;
  streamingContent: string;
  abortController: AbortController | null;

  fetchConversations: () => Promise<void>;
  createConversation: (title: string, mode: string, modelId?: string) => Promise<Conversation | null>;
  deleteConversation: (id: string) => Promise<void>;
  updateConversation: (id: string, data: Partial<Conversation>) => Promise<void>;
  fetchMessages: (conversationId: string, page?: number) => Promise<void>;
  saveMessage: (convId: string, role: string, content: string, modelId?: string) => Promise<void>;
  deleteMessage: (messageId: string) => Promise<void>;
  sendChatMessage: (convId: string, message: string, modelId: string, imageUrls?: string[]) => Promise<void>;
  stopStreaming: () => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (content: string) => void;
  clearMessages: () => void;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversations: [],
  currentMessages: [],
  isLoadingConversations: false,
  isLoadingMessages: false,
  isStreaming: false,
  streamingContent: '',
  abortController: null,

  fetchConversations: async () => {
    set({ isLoadingConversations: true });
    try {
      const guestId = useAuthStore.getState().guestId;
      const headers: Record<string, string> = {};
      if (guestId && !useAuthStore.getState().isLoggedIn) {
        headers['x-guest-id'] = guestId;
      }
      const resp = await fetch('/api/conversations', { credentials: 'include', headers });
      const data = await resp.json();
      set({ conversations: data, isLoadingConversations: false });
    } catch {
      set({ isLoadingConversations: false });
    }
  },

  createConversation: async (title, mode, modelId) => {
    const guestId = useAuthStore.getState().guestId;
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (guestId && !useAuthStore.getState().isLoggedIn) {
      headers['x-guest-id'] = guestId;
    }
    try {
      const resp = await fetch('/api/conversations', {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({ title, mode, model_id: modelId }),
      });
      if (resp.ok) {
        const conv = await resp.json();
        set((s) => ({ conversations: [conv, ...s.conversations] }));
        return conv;
      }
    } catch (e) {
      console.error('Create conversation failed:', e);
    }
    return null;
  },

  deleteConversation: async (id) => {
    const guestId = useAuthStore.getState().guestId;
    const headers: Record<string, string> = {};
    if (guestId && !useAuthStore.getState().isLoggedIn) {
      headers['x-guest-id'] = guestId;
    }
    try {
      await fetch(`/api/conversations/${id}`, {
        method: 'DELETE',
        credentials: 'include',
        headers,
      });
      set((s) => ({
        conversations: s.conversations.filter((c) => c.id !== id),
      }));
    } catch (e) {
      console.error('Delete conversation failed:', e);
    }
  },

  updateConversation: async (id, data) => {
    try {
      await fetch(`/api/conversations/${id}`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      set((s) => ({
        conversations: s.conversations.map((c) =>
          c.id === id ? { ...c, ...data } : c
        ),
      }));
    } catch (e) {
      console.error('Update conversation failed:', e);
    }
  },

  fetchMessages: async (conversationId, page = 1) => {
    set({ isLoadingMessages: true });
    const guestId = useAuthStore.getState().guestId;
    const headers: Record<string, string> = {};
    if (guestId && !useAuthStore.getState().isLoggedIn) {
      headers['x-guest-id'] = guestId;
    }
    try {
      const resp = await fetch(
        `/api/conversations/${conversationId}/messages?page=${page}&page_size=50`,
        { credentials: 'include', headers }
      );
      const data = await resp.json();
      if (page === 1) {
        set({ currentMessages: data.messages || [], isLoadingMessages: false });
      } else {
        set((s) => ({
          currentMessages: [...(data.messages || []), ...s.currentMessages],
          isLoadingMessages: false,
        }));
      }
    } catch {
      set({ isLoadingMessages: false });
    }
  },

  saveMessage: async (convId, role, content, modelId) => {
    const guestId = useAuthStore.getState().guestId;
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (guestId && !useAuthStore.getState().isLoggedIn) {
      headers['x-guest-id'] = guestId;
    }
    try {
      const resp = await fetch(`/api/conversations/${convId}/messages`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({ role, content, model_id: modelId, status: 'completed' }),
      });
      if (resp.ok) {
        const msg = await resp.json();
        set((s) => ({
          currentMessages: [...s.currentMessages, msg],
        }));
      }
    } catch (e) {
      console.error('Save message failed:', e);
    }
  },

  deleteMessage: async (messageId) => {
    try {
      await fetch(`/api/messages/${messageId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      set((s) => ({
        currentMessages: s.currentMessages.filter((m) => m.id !== messageId),
      }));
    } catch (e) {
      console.error('Delete message failed:', e);
    }
  },

  sendChatMessage: async (convId, message, modelId, imageUrls) => {
    const abortController = new AbortController();
    set({ isStreaming: true, streamingContent: '', abortController });

    // Add user message to list immediately
    const userMsg: Message = {
      id: 'temp-' + Date.now(),
      conversation_id: convId,
      role: 'user',
      content: message,
      model_id: modelId,
      status: 'completed',
      created_at: new Date().toISOString(),
    };
    set((s) => ({ currentMessages: [...s.currentMessages, userMsg] }));

    // Save user message to backend
    const guestId = useAuthStore.getState().guestId;
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (guestId && !useAuthStore.getState().isLoggedIn) {
      headers['x-guest-id'] = guestId;
    }
    try {
      const saveResp = await fetch(`/api/conversations/${convId}/messages`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({ role: 'user', content: message, model_id: modelId, status: 'completed' }),
      });
      if (saveResp.ok) {
        const savedMsg = await saveResp.json();
        set((s) => ({
          currentMessages: s.currentMessages.map((m) =>
            m.id === userMsg.id ? savedMsg : m
          ),
        }));
      }
    } catch {}

    // Start streaming
    let fullContent = '';
    try {
      const resp = await fetch('/api/chat/stream', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: convId,
          model_id: modelId,
          message,
          image_urls: imageUrls,
        }),
        signal: abortController.signal,
      });

      const reader = resp.body?.getReader();
      if (!reader) throw new Error('No reader');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                fullContent += parsed.content;
                set({ streamingContent: fullContent });
              }
              if (parsed.error) {
                useUIStore.getState().showToast(parsed.error, 'error');
              }
            } catch {}
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        useUIStore.getState().showToast('Stream failed: ' + err.message, 'error');
      }
    }

    set({ isStreaming: false });

    // Save assistant message
    if (fullContent) {
      const assistantMsg: Message = {
        id: 'temp-assistant-' + Date.now(),
        conversation_id: convId,
        role: 'assistant',
        content: fullContent,
        model_id: modelId,
        status: 'completed',
        created_at: new Date().toISOString(),
      };
      set((s) => ({ currentMessages: [...s.currentMessages, assistantMsg] }));

      // Save to backend
      try {
        const saveResp = await fetch(`/api/conversations/${convId}/messages`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: 'assistant', content: fullContent, model_id: modelId, status: 'completed' }),
        });
        if (saveResp.ok) {
          const savedMsg = await saveResp.json();
          set((s) => ({
            currentMessages: s.currentMessages.map((m) =>
              m.id === assistantMsg.id ? savedMsg : m
            ),
          }));
        }
      } catch {}

      // Refresh conversation list
      get().fetchConversations();
    }

    set({ streamingContent: '', abortController: null });
  },

  stopStreaming: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
      set({ isStreaming: false, abortController: null });
    }
  },

  setStreamingContent: (content) => set({ streamingContent: content }),
  appendStreamingContent: (content) => set((s) => ({ streamingContent: s.streamingContent + content })),
  clearMessages: () => set({ currentMessages: [] }),
}));
