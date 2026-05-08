import { useUIStore, useAuthStore, useConversationStore } from '../../store';
import Sidebar from './Sidebar';
import ChatView from '../chat/ChatView';
import VoiceView from '../voice/VoiceView';
import { useEffect } from 'react';

export default function Layout() {
  const { mode, sidebarOpen, setSidebarOpen, setCurrentConversationId } = useUIStore();
  const { isLoggedIn } = useAuthStore();
  const { fetchConversations } = useConversationStore();

  useEffect(() => {
    fetchConversations();
  }, [isLoggedIn]);

  const handleNewChat = () => {
    setCurrentConversationId(null);
  };

  return (
    <div className="h-full flex flex-col bg-primary-50 relative">
      {/* Top bar */}
      <header className="flex-shrink-0 flex items-center justify-between px-4 py-3 bg-white/80 backdrop-blur-sm border-b border-primary-100 z-10">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 -ml-1 rounded-lg hover:bg-primary-100 transition-colors"
          aria-label="Open sidebar"
        >
          <svg className="w-6 h-6 text-primary-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <h1 className="text-lg font-semibold text-gray-800">
          {mode === 'chat' ? 'AI Chat' : 'AI Voice'}
        </h1>

        <button
          onClick={handleNewChat}
          className="p-2 -mr-1 rounded-lg hover:bg-primary-100 transition-colors"
          aria-label="New conversation"
        >
          <svg className="w-6 h-6 text-primary-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        {mode === 'chat' ? <ChatView /> : <VoiceView />}
      </main>

      {/* Sidebar overlay */}
      <Sidebar />

      {/* Shadow overlay when sidebar is open */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
