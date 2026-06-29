import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Models from './pages/Models'
import Chat from './pages/Chat'
import Settings from './pages/Settings'
import APIKeys from './pages/APIKeys'
import Monitoring from './pages/Monitoring'
import HuggingFace from './pages/HuggingFace'
import FunctionTester from './pages/FunctionTester'
import RAGManager from './pages/RAGManager'
import BatchProcessor from './pages/BatchProcessor'
import AdminDashboard from './pages/AdminDashboard'
import LoRAManager from './pages/LoRAManager'
import DatasetManager from './pages/DatasetManager'
import MultiModalManager from './pages/MultiModalManager'
import Downloads from './pages/Downloads'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/models" element={<Models />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/huggingface" element={<HuggingFace />} />
        <Route path="/downloads" element={<Downloads />} />
        <Route path="/functions" element={<FunctionTester />} />
        <Route path="/rag" element={<RAGManager />} />
        <Route path="/batch" element={<BatchProcessor />} />
        <Route path="/api-keys" element={<APIKeys />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/lora" element={<LoRAManager />} />
        <Route path="/datasets" element={<DatasetManager />} />
        <Route path="/multimodal" element={<MultiModalManager />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App

