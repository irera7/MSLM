import { useEffect } from 'react';

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  callback: () => void;
  description?: string;
}

export function useKeyboardShortcut(shortcuts: ShortcutConfig[]) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      shortcuts.forEach(shortcut => {
        const ctrlMatch = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = shortcut.alt ? event.altKey : !event.altKey;
        const metaMatch = shortcut.meta ? event.metaKey : !event.metaKey;

        if (
          event.key.toLowerCase() === shortcut.key.toLowerCase() &&
          ctrlMatch &&
          shiftMatch &&
          altMatch &&
          (shortcut.meta === undefined || metaMatch)
        ) {
          event.preventDefault();
          shortcut.callback();
        }
      });
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

// Predefined shortcuts
export const shortcuts = {
  newChat: { key: 'n', ctrl: true, description: 'New Chat' },
  search: { key: 'k', ctrl: true, description: 'Search' },
  save: { key: 's', ctrl: true, description: 'Save' },
  send: { key: 'Enter', ctrl: true, description: 'Send Message' },
  escape: { key: 'Escape', description: 'Close/Cancel' },
  settings: { key: ',', ctrl: true, description: 'Settings' },
};

