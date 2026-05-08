import { useState } from 'react';
import { useUIStore, useAuthStore, useModelStore } from '../../store';

const SPEAKERS = [
  { value: 'vv', label: 'vv - 默认女声' },
  { value: 'xiaohe', label: '小荷 - 温柔女声' },
  { value: 'yunzhou', label: '云舟 - 沉稳男声' },
  { value: 'xiaotian', label: '小天 - 活泼女声' },
  { value: 'zhichu', label: '之初 - 磁性男声' },
];

export default function SettingsModal() {
  const { setShowSettingsModal, showToast } = useUIStore();
  const { user, fetchMe } = useAuthStore();
  const { models, selectedModelId, setSelectedModel } = useModelStore();
  const [nickname, setNickname] = useState(user?.nickname || '');
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
  const [ttsSpeaker, setTtsSpeaker] = useState('vv');
  const [defaultModel, setDefaultModel] = useState(selectedModelId);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Update user profile
      const resp = await fetch('/api/auth/me', {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname: nickname || undefined, avatar_url: avatarUrl || undefined }),
      });
      if (resp.ok) {
        await fetchMe();
      }

      // Update settings
      await fetch('/api/auth/me/settings', {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tts_speaker: ttsSpeaker,
          default_model_id: defaultModel,
        }),
      });

      setSelectedModel(defaultModel);
      showToast('设置已保存', 'success');
      setShowSettingsModal(false);
    } catch {
      showToast('保存失败', 'error');
    }
    setIsSaving(false);
  };

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      setAvatarUrl(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  return (
    <div
      className="fixed inset-0 bg-black/30 z-50 flex items-end md:items-center justify-center"
      onClick={() => setShowSettingsModal(false)}
    >
      <div
        className="bg-white rounded-t-2xl md:rounded-2xl shadow-xl p-6 w-full max-w-md max-h-[85vh] overflow-y-auto animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-gray-800 mb-5">个人设置</h3>

        {/* Avatar */}
        <div className="flex items-center gap-4 mb-5">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-xl font-bold overflow-hidden">
            {avatarUrl ? (
              <img src={avatarUrl} alt="" className="w-full h-full object-cover" />
            ) : (
              (user?.nickname || user?.username || 'U').charAt(0).toUpperCase()
            )}
          </div>
          <div>
            <label className="cursor-pointer px-4 py-2 rounded-lg bg-primary-50 text-primary-700 text-sm hover:bg-primary-100 transition-colors">
              上传头像
              <input type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} />
            </label>
            <p className="text-xs text-gray-400 mt-1">支持 JPG/PNG/GIF</p>
          </div>
        </div>

        {/* Nickname */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-600 mb-1.5">昵称</label>
          <input
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="输入昵称"
            className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-300 text-sm"
          />
        </div>

        {/* Default model */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-600 mb-1.5">默认 LLM 模型</label>
          <select
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-300 text-sm"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </div>

        {/* TTS speaker */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-600 mb-1.5">默认 TTS 音色</label>
          <select
            value={ttsSpeaker}
            onChange={(e) => setTtsSpeaker(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-300 text-sm"
          >
            {SPEAKERS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={() => setShowSettingsModal(false)}
            className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex-1 py-2.5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white font-medium transition-colors disabled:opacity-50"
          >
            {isSaving ? '保存中...' : '保存'}
          </button>
        </div>

        {/* Version */}
        <p className="text-center text-xs text-gray-400 mt-5">AI Chat v1.0.0</p>
      </div>
    </div>
  );
}
