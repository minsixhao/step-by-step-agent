import { useUIStore } from '../../store';

export default function Toast() {
  const { toastMessage, toastType, hideToast } = useUIStore();

  if (!toastMessage) return null;

  const bgColor = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-primary-500',
  }[toastType];

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 toast-enter">
      <div className={`${bgColor} text-white px-5 py-3 rounded-xl shadow-lg flex items-center gap-3 max-w-sm`}>
        <span className="text-sm font-medium flex-1">{toastMessage}</span>
        <button onClick={hideToast} className="text-white/80 hover:text-white">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
