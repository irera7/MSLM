import { Link, useLocation } from 'react-router-dom'
import { 
  Home, 
  Database, 
  MessageSquare, 
  Settings,
  Download,
  Activity,
  Key,
  BarChart3,
  Globe,
  Code,
  Layers,
  Shield,
  Wand2,
  FolderOpen,
  ImageIcon
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface SidebarProps {
  isOpen: boolean
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Admin Panel', href: '/admin', icon: Shield },
  { name: 'Models', href: '/models', icon: Database },
  { name: 'Downloads', href: '/downloads', icon: Download },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'HuggingFace', href: '/huggingface', icon: Globe },
  { name: 'Functions', href: '/functions', icon: Code },
  { name: 'RAG', href: '/rag', icon: Database },
  { name: 'Batch', href: '/batch', icon: Layers },
  { name: 'LoRA / Fine-tune', href: '/lora', icon: Wand2 },
  { name: 'Datasets', href: '/datasets', icon: FolderOpen },
  { name: 'Multi-Modal', href: '/multimodal', icon: ImageIcon },
  { name: 'API Keys', href: '/api-keys', icon: Key },
  { name: 'Monitoring', href: '/monitoring', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar({ isOpen }: SidebarProps) {
  const location = useLocation()

  if (!isOpen) return null

  return (
    <div className="w-64 bg-card border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-bold text-primary">LM Studio</h1>
        <p className="text-sm text-muted-foreground">Clone</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                'hover:bg-accent hover:text-accent-foreground',
                isActive && 'bg-primary text-primary-foreground hover:bg-primary/90'
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Activity className="w-4 h-4" />
          <span>v1.0.0</span>
        </div>
      </div>
    </div>
  )
}

