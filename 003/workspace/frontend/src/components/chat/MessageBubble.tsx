import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeHighlight from 'rehype-highlight';
import rehypeKatex from 'rehype-katex';
import type { Message as MessageType } from '../../types';
import { useConversationStore, useUIStore } from '../../store';

interface Props {
  message: MessageType;
  isStreaming?: boolean;
}

export default function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user';
  const [showMenu, setShowMenu] = useState(false);
  const [isLongPress, setIsLongPress] = useState(false);
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { deleteMessage } = useConversationStore();
  const { showToast } = useUIStore();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      showToast('已复制到剪贴板', 'success');
    } catch {
      showToast('复制失败', 'error');
    }
    setShowMenu(false);
  };

  const handleDelete = async () => {
    if (confirm('确认删除这条消息？')) {
      await deleteMessage(message.id);
    }
    setShowMenu(false);
  };

  // Touch handlers for long press
  const handleTouchStart = () => {
    longPressTimer.current = setTimeout(() => {
      setIsLongPress(true);
      setShowMenu(true);
    }, 600);
  };

  const handleTouchEnd = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  };

  useEffect(() => {
    return () => {
      if (longPressTimer.current) clearTimeout(longPressTimer.current);
    };
  }, []);

  return (
    <div
      className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
      onMouseEnter={() => !isUser && setShowMenu(true)}
      onMouseLeave={() => !isLongPress && setShowMenu(false)}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      <div className={`relative max-w-[85%] md:max-w-[75%] ${isUser ? 'order-1' : 'order-1'}`}>
        {/* Message bubble */}
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-primary-500 text-white rounded-br-md'
              : 'bg-white text-gray-800 rounded-bl-md shadow-sm border border-gray-100'
          }`}
        >
          {isUser ? (
            // User message - plain text with inline images
            <div className="whitespace-pre-wrap break-words">{message.content}</div>
          ) : (
            // Assistant message - Markdown rendered
            <div className="markdown-body">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeHighlight, rehypeKatex]}
              >
                {message.content}
              </ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-primary-500 animate-pulse ml-0.5 align-text-bottom" />
              )}
            </div>
          )}
        </div>

        {/* Action menu */}
        {showMenu && !isUser && !isStreaming && (
          <div
            className={`absolute ${isUser ? 'right-0' : 'left-0'} -bottom-9 flex gap-1 bg-white rounded-lg shadow-lg border border-gray-100 px-1.5 py-1 z-10`}
          >
            <button onClick={handleCopy} className="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-primary-600" title="复制">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
            <button onClick={handleDelete} className="p-1.5 rounded hover:bg-red-50 text-gray-500 hover:text-red-500" title="删除">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        )}

        {/* Timestamp */}
        {message.created_at && !isStreaming && (
          <div className={`text-[10px] text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {new Date(message.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  );
}
