import { useState } from 'react'
import { GlobalProvider } from './store/globalContext'
import Sidebar from './components/Chat/Sidebar'
import ChatWindow from './components/Chat/ChatWindow'
import AdminPortal from './components/Admin/AdminPortal'

function AppContent() {
  const [showAdmin, setShowAdmin] = useState(false)

  return (
    <div className="flex h-screen bg-[#0d0f12] overflow-hidden">
      <Sidebar onAddProject={() => setShowAdmin(true)} />

      <main className="flex-1 flex flex-col min-w-0">
        <ChatWindow />
      </main>

      {showAdmin && (
        <AdminPortal onClose={() => setShowAdmin(false)} />
      )}
    </div>
  )
}

export default function App() {
  return (
    <GlobalProvider>
      <AppContent />
    </GlobalProvider>
  )
}
