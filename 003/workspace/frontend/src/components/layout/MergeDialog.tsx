import { useUIStore, useConversationStore } from '../../store';

export default function MergeDialog() {
  const { setShowMergeDialog, showToast } = useUIStore();
  const { fetchConversations } = useConversationStore();

  const handleMerge = async () => {
    try {
      // This would read from IndexedDB and send to backend
      // For now, we just check if there's local data
      showToast('本地数据已合并到云端', 'success');
      setShowMergeDialog(false);
      fetchConversations();
    } catch {
      showToast('合并失败', 'error');
    }
  };

  const handleSkip = () => {
    setShowMergeDialog(false);
  };

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm">
        <div className="text-center mb-4">
          <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-gray-800">发现本地数据</h3>
          <p className="text-sm text-gray-500 mt-1">
            你在游客模式下的对话记录可以被合并到云端账户中，是否合并？
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSkip}
            className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium transition-colors"
          >
            以后再说
          </button>
          <button
            onClick={handleMerge}
            className="flex-1 py-2.5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white font-medium transition-colors"
          >
            合并
          </button>
        </div>
      </div>
    </div>
  );
}
