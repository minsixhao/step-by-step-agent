import { useEffect } from 'react'
import { useAuthStore, useUIStore } from './store'
import Layout from './components/layout/Layout'
import SettingsModal from './components/layout/SettingsModal'
import MergeDialog from './components/layout/MergeDialog'
import Toast from './components/common/Toast'

function App() {
  const { fetchMe } = useAuthStore()
  const { showSettingsModal, showMergeDialog } = useUIStore()

  useEffect(() => {
    fetchMe()
  }, [])

  return (
    <div className="h-screen w-screen overflow-hidden bg-white">
      <Layout />
      {showSettingsModal && <SettingsModal />}
      {showMergeDialog && <MergeDialog />}
      <Toast />
    </div>
  )
}

export default App
