import { useState, useRef, useEffect } from 'react';
import { useModelStore, useUIStore } from '../../store';

interface Props {
  onSend: (text: string, imageUrls?: string[]) => void;
  onStop: () => void;
  isStreaming: boolean;
}

export default function ChatInput({ onSend, onStop, isStreaming }: Props) {
  const [text, setText] = useState('');
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { models, selectedModelId } = useModelStore();
  const { showModelSelector, setShowModelSelector, showToast } = useUIStore();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [text]);

  // Focus on mount and when mode switches
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isStreaming) return;
    onSend(trimmed, imageUrls.length > 0 ? imageUrls : undefined);
    setText('');
    setImageUrls([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append('file', file);
        const resp = await fetch('/api/upload/image', {
          method: 'POST',
          credentials: 'include',
          body: formData,
        });
        if (resp.ok) {
          const data = await resp.json();
          setImageUrls((prev) => [...prev, data.url]);
        }
      }
    } catch {
      showToast('上传失败', 'error');
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const selectedModel = models.find((m) => m.id === selectedModelId);

  return (
    <div className="flex-shrink-0 px-3 pb-3 pt-1">
      <div className="max-w-chat mx-auto">
        <div className="bg-white rounded-2xl shadow-lg border border-primary-100">
          {/* Image previews */}
          {imageUrls.length > 0 && (
            <div className="flex gap-2 px-4 pt-3 flex-wrap">
              {imageUrls.map((url, idx) => (
                <div key={idx} className="relative group">
                  <img src={url} alt="" className="w-16 h-16 object-cover rounded-lg border" />
                  <button
                    onClick={() => setImageUrls((prev) => prev.filter((_, i) => i !== idx))}
                    className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Text input */}
          <div className="flex items-end gap-2 px-3 py-2">
            <textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入消息..."
              rows={1}
              className="flex-1 resize-none bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none py-2 max-h-[150px]"
              disabled={isStreaming}
            />

            <div className="flex items-center gap-1 flex-shrink-0">
              {/* Upload button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="p-2 rounded-lg text-gray-400 hover:text-primary-500 hover:bg-primary-50 transition-colors"
                title="上传图片"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={handleUpload}
              />

              {/* Send / Stop button */}
              {isStreaming ? (
                <button
                  onClick={onStop}
                  className="p-2 rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors"
                  title="停止生成"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <rect x="6" y="6" width="12" height="12" rx="2" />
                  </svg>
                </button>
              ) : (
                <button
                  onClick={handleSend}
                  disabled={!text.trim()}
                  className="p-2 rounded-lg bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  title="发送"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Bottom bar: model selector */}
          <div className="flex items-center px-3 pb-2">
            <button
              onClick={() => setShowModelSelector(!showModelSelector)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs text-gray-500 hover:bg-primary-50 hover:text-primary-600 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              {selectedModel?.name || '选择模型'}
            </button>

            {showModelSelector && (
              <ModelSelector onClose={() => setShowModelSelector(false)} />
            )}
          </div>
        </div>

        <p className="text-[10px] text-center text-gray-400 mt-1.5">
          AI 生成内容可能不准确，请核实重要信息
        </p>
      </div>
    </div>
  );
}

function ModelSelector({ onClose }: { onClose: () => void }) {
  const { models, selectedModelId, setSelectedModel } = useModelStore();
  const [search, setSearch] = useState('');

  const filtered = models.filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="absolute bottom-full left-3 mb-2 w-72 max-h-80 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-20">
      <div className="p-2 border-b border-gray-100">
        <input
          type="text"
          placeholder="搜索模型..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-3 py-1.5 text-sm rounded-lg bg-gray-50 focus:outline-none focus:ring-1 focus:ring-primary-300"
          autoFocus
        />
      </div>
      <div className="overflow-y-auto max-h-60">
        {filtered.map((m) => (
          <button
            key={m.id}
            onClick={() => {
              setSelectedModel(m.id);
              onClose();
            }}
            className={`w-full text-left px-3 py-2.5 text-sm hover:bg-primary-50 transition-colors flex items-center justify-between ${
              m.id === selectedModelId ? 'bg-primary-50 text-primary-700' : 'text-gray-700'
            }`}
          >
            <span className="truncate">{m.name}</span>
            {m.id === selectedModelId && (
              <svg className="w-4 h-4 text-primary-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
