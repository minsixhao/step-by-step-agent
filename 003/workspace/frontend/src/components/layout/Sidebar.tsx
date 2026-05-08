import { useState, useMemo } from 'react';
import { useUIStore, useAuthStore, useConversationStore } from '../../store';
import type { Conversation } from '../../types';

export default function Sidebar() {
  const { sidebarOpen, setSidebarOpen, setCurrentConversationId, currentConversationId, setMode, mode } = useUIStore();
  const { user, isLoggedIn } = useAuthStore();
  const { conversations, deleteConversation } = useConversationStore();
  const [searchText, setSearchText] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);

  const filteredConversations = useMemo(() => {
    if (!searchText.trim()) return conversations;
    const q = searchText.toLowerCase();
    return conversations.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        c.last_message_preview?.toLowerCase().includes(q)
    );
  }, [conversations, searchText]);

  // Group by time
  const grouped = useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 86400000);

    const groups: { label: string; items: Conversation[] }[] = [];
    const todayItems: Conversation[] = [];
    const yesterdayItems: Conversation[] = [];
    const olderItems: Conversation[] = [];

    filteredConversations.forEach((c) => {
      const d = c.created_at ? new Date(c.created_at) : now;
      if (d >= today) todayItems.push(c);
      else if (d >= yesterday) yesterdayItems.push(c);
      else olderItems.push(c);
    });

    if (todayItems.length) groups.push({ label: '今天', items: todayItems });
    if (yesterdayItems.length) groups.push({ label: '昨天', items: yesterdayItems });
    if (olderItems.length) groups.push({ label: '更早', items: olderItems });

    return groups;
  }, [filteredConversations]);

  const handleSelectConversation = (id: string) => {
    setCurrentConversationId(id);
    setSidebarOpen(false);
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('确认删除这个对话？')) {
      await deleteConversation(id);
      if (currentConversationId === id) {
        setCurrentConversationId(null);
      }
    }
  };

  const handleNewChat = () => {
    setCurrentConversationId(null);
    setSidebarOpen(false);
  };

  const handleModeSwitch = (newMode: 'chat' | 'voice') => {
    setMode(newMode);
    setCurrentConversationId(null);
    setSidebarOpen(false);
  };

  return (
    <>
      {/* Sidebar drawer */}
      <div
        className={`fixed top-0 left-0 h-full bg-white shadow-2xl z-30 transition-transform duration-300 ease-in-out w-[80vw] max-w-[400px] flex flex-col ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex-shrink-0 px-4 py-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold text-gray-800">历史对话</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Mode switch */}
          <div className="flex rounded-lg bg-primary-50 p-0.5 mb-3">
            <button
              onClick={() => handleModeSwitch('chat')}
              className={`flex-1 py-1.5 text-sm rounded-md transition-colors ${
                mode === 'chat' ? 'bg-white text-primary-700 font-medium shadow-sm' : 'text-gray-500'
              }`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => handleModeSwitch('voice')}
              className={`flex-1 py-1.5 text-sm rounded-md transition-colors ${
                mode === 'voice' ? 'bg-white text-primary-700 font-medium shadow-sm' : 'text-gray-500'
              }`}
            >
              🎧 Voice
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <svg className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="搜索对话..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-transparent"
            />
          </div>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto">
          {grouped.map((group) => (
            <div key={group.label} className="px-3 py-2">
              <div className="text-xs text-gray-400 font-medium px-3 py-1.5 uppercase tracking-wider">
                {group.label}
              </div>
              {group.items.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv.id)}
                  className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors mb-0.5 ${
                    currentConversationId === conv.id
                      ? 'bg-primary-100 text-primary-800'
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <span className="text-lg flex-shrink-0">
                    {conv.mode === 'voice' ? '🎧' : '💬'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{conv.title}</div>
                    {conv.last_message_preview && (
                      <div className="text-xs text-gray-400 truncate mt-0.5">
                        {conv.last_message_preview}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={(e) => handleDeleteConversation(e, conv.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100 text-gray-400 hover:text-red-500 transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          ))}

          {filteredConversations.length === 0 && (
            <div className="text-center text-gray-400 py-12">
              <div className="text-4xl mb-3">💬</div>
              <p className="text-sm">{searchText ? '没有找到匹配的对话' : '还没有对话记录'}</p>
              <button
                onClick={handleNewChat}
                className="mt-3 text-sm text-primary-500 hover:text-primary-600 font-medium"
              >
                开始新对话
              </button>
            </div>
          )}
        </div>

        {/* User info footer */}
        <div className="flex-shrink-0 border-t border-gray-100 p-3">
          <button
            onClick={() => setShowUserMenu(true)}
            className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-sm font-bold overflow-hidden">
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="" className="w-full h-full object-cover" />
              ) : (
                (user?.nickname || user?.username || '游').charAt(0).toUpperCase()
              )}
            </div>
            <div className="flex-1 text-left">
              <div className="text-sm font-medium text-gray-800">
                {isLoggedIn ? (user?.nickname || user?.username) : '游客'}
              </div>
              <div className="text-xs text-gray-400">
                {isLoggedIn ? user?.username : '点击登录'}
              </div>
            </div>
            <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      {/* User menu modal */}
      {showUserMenu && <UserMenu onClose={() => setShowUserMenu(false)} />}
    </>
  );
}

function UserMenu({ onClose }: { onClose: () => void }) {
  const { user, isLoggedIn, logout } = useAuthStore();
  const { setShowSettingsModal } = useUIStore();

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    logout();
    onClose();
  };

  const handleOpenSettings = () => {
    setShowSettingsModal(true);
    onClose();
  };

  if (!isLoggedIn) {
    return (
      <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4" onClick={onClose}>
        <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
          <h3 className="text-lg font-bold text-gray-800 mb-4">登录 / 注册</h3>
          <AuthForm onClose={onClose} />
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-end md:items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded-t-2xl md:rounded-2xl shadow-xl p-6 w-full max-w-sm animate-slide-up" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-lg font-bold">
            {(user?.nickname || user?.username || 'U').charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="font-semibold text-gray-800">{user?.nickname || user?.username}</div>
            <div className="text-sm text-gray-500">@{user?.username}</div>
          </div>
        </div>

        <div className="space-y-1">
          <button
            onClick={handleOpenSettings}
            className="w-full text-left px-4 py-2.5 rounded-lg hover:bg-gray-50 flex items-center gap-3 text-gray-700"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            个人设置
          </button>
          <button
            onClick={handleLogout}
            className="w-full text-left px-4 py-2.5 rounded-lg hover:bg-red-50 flex items-center gap-3 text-red-600"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            退出登录
          </button>
        </div>
        <button onClick={onClose} className="w-full mt-3 py-2 text-sm text-gray-400 hover:text-gray-600">
          取消
        </button>
      </div>
    </div>
  );
}

function AuthForm({ onClose }: { onClose: () => void }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [nickname, setNickname] = useState('');
  const [error, setError] = useState('');
  const { fetchMe } = useAuthStore();
  const { showToast } = useUIStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
    const body: Record<string, string> = { username, password };
    if (!isLogin && nickname) body.nickname = nickname;

    try {
      const resp = await fetch(endpoint, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (resp.ok) {
        await fetchMe();
        showToast(isLogin ? '登录成功' : '注册成功', 'success');
        onClose();
      } else {
        const data = await resp.json();
        setError(data.detail || '操作失败');
      }
    } catch {
      setError('网络错误，请重试');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <input
        type="text"
        placeholder="用户名"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-300 text-sm"
        required
        minLength={3}
      />
      <input
        type="password"
        placeholder="密码"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-300 text-sm"
        required
        minLength={6}
      />
      {!isLogin && (
        <input
          type="text"
          placeholder="昵称（可选）"
          value={nickname}
          onChange={(e) => setNickname(e.target.value)}
          className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-300 text-sm"
        />
      )}
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button
        type="submit"
        className="w-full py-2.5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white font-medium transition-colors"
      >
        {isLogin ? '登录' : '注册'}
      </button>
      <button
        type="button"
        onClick={() => { setIsLogin(!isLogin); setError(''); }}
        className="w-full text-sm text-primary-500 hover:text-primary-600"
      >
        {isLogin ? '没有账号？去注册' : '已有账号？去登录'}
      </button>
    </form>
  );
}
