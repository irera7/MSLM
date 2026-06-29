import { Menu, Sun, Moon } from 'lucide-react'

interface HeaderProps {
  onToggleSidebar: () => void
  onToggleTheme: () => void
  theme: 'light' | 'dark'
}

export default function Header({ onToggleSidebar, onToggleTheme, theme }: HeaderProps) {
  return (
    <header className="h-16 border-b border-border bg-card px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={onToggleTheme}
          className="p-2 hover:bg-accent rounded-lg transition-colors"
        >
          {theme === 'light' ? (
            <Moon className="w-5 h-5" />
          ) : (
            <Sun className="w-5 h-5" />
          )}
        </button>
      </div>
    </header>
  )
}

