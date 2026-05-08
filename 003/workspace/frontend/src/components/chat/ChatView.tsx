import { useEffect, useRef, useState } from 'react';
import { useUIStore, useConversationStore, useAuthStore, useModelStore } from '../../store';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import LoadingDots from '../common/LoadingDots';

export default function ChatView() {
  const { currentConversationId } = useUIStore();
  const {
    currentMessages, isLoadingMessages, isStreaming, streamingContent,
    fetchMessages, sendChatMessage, stopStreaming, clearMessages,
  } = useConversationStore();
  const { selectedModelId } = useModelStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isUserScrolling, setIsUserScrolling] = useState(false);

  // Load messages when conversation changes
  useEffect(() => {
    if (currentConversationId) {
      fetchMessages(currentConversationId);
    } else {
      clearMessages();
    }
  }, [currentConversationId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (!isUserScrolling) {
      scrollToBottom();
    }
  }, [currentMessages, streamingContent]);

  const scrollToBottom = (smooth = true) => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
    }
    setShowScrollButton(false);
    setIsUserScrolling(false);
  };

  const handleScroll = () => {
    const container = messagesContainerRef.current;
    if (!container) return;
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    setShowScrollButton(!isNearBottom);
    if (isNearBottom) setIsUserScrolling(false);
    else setIsUserScrolling(true);
  };

  const handleSendMessage = async (text: string, imageUrls?: string[]) => {
    let convId = currentConversationId;
    if (!convId) {
      // Create new conversation
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
          body: JSON.stringify({ title: text.slice(0, 30), mode: 'chat', model_id: selectedModelId }),
        });
        if (resp.ok) {
          const conv = await resp.json();
          convId = conv.id;
          useUIStore.getState().setCurrentConversationId(conv.id);
        }
      } catch (e) {
        console.error(e);
        return;
      }
    }

    if (convId) {
      await sendChatMessage(convId, text, selectedModelId, imageUrls);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-4"
      >
        <div className="max-w-chat mx-auto">
          {!currentConversationId && currentMessages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center mb-6">
                <svg className="w-10 h-10 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-700 mb-2">开始对话</h2>
              <p className="text-gray-400 text-sm max-w-xs">
                在下方输入你想了解的内容，AI 将为你提供帮助
              </p>
            </div>
          )}

          {isLoadingMessages && (
            <div className="flex justify-center py-8">
              <LoadingDots />
            </div>
          )}

          {currentMessages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Streaming message */}
          {isStreaming && streamingContent && (
            <MessageBubble
              message={{
                id: 'streaming',
                conversation_id: currentConversationId || '',
                role: 'assistant',
                content: streamingContent,
                status: 'sending',
                created_at: new Date().toISOString(),
              }}
              isStreaming
            />
          )}

          {isStreaming && !streamingContent && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                <LoadingDots />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <button
          onClick={() => scrollToBottom(true)}
          className="absolute bottom-24 right-6 w-10 h-10 rounded-full bg-primary-500 text-white shadow-lg flex items-center justify-center hover:bg-primary-600 transition-colors z-10"
          aria-label="回到底部"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>
      )}

      {/* Input area */}
      <ChatInput
        onSend={handleSendMessage}
        onStop={stopStreaming}
        isStreaming={isStreaming}
      />
    </div>
  );
}
