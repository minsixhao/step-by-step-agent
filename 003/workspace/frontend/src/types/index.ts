export interface User {
  id: string;
  username: string;
  nickname: string;
  avatar_url: string;
  created_at?: string;
}

export interface UserSettings {
  id: string;
  theme: string;
  default_model_id: string;
  tts_speaker: string;
  extra_settings: Record<string, any>;
}

export interface Conversation {
  id: string;
  user_id?: string;
  title: string;
  mode: 'chat' | 'voice';
  model_id?: string;
  summary?: string;
  is_archived: boolean;
  created_at?: string;
  updated_at?: string;
  last_message_at?: string;
  last_message_preview?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  model_id?: string;
  tokens_used?: number;
  status: 'sending' | 'completed' | 'failed';
  error_message?: string;
  created_at?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  context_length?: number;
  pricing?: Record<string, any>;
}
