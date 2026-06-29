import { useState } from 'react';
import { Edit2, RefreshCw, GitBranch, Download, Send } from 'lucide-react';
import { useToast } from '../components/ToastProvider';
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function EnhancedChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');
  const toast = useToast();

  // Keyboard shortcuts
  useKeyboardShortcut([
    {
      key: 'Enter',
      ctrl: true,
      callback: () => handleSend(),
      description: 'Send message'
    },
    {
      key: 'n',
      ctrl: true,
      callback: () => handleNewChat(),
      description: 'New chat'
    }
  ]);

  const handleSend = async () => {
    if (!input.trim()) return;

    try {
      // Add user message
      const userMessage: Message = {
        id: Date.now(),
        role: 'user',
        content: input,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, userMessage]);
      setInput('');

      // Simulate API call
      toast.info('Sending message...');
      
      // TODO: Replace with actual API call
      setTimeout(() => {
        const assistantMessage: Message = {
          id: Date.now() + 1,
          role: 'assistant',
          content: 'This is a simulated response. Connect to backend for real responses.',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, assistantMessage]);
        toast.success('Response received!');
      }, 1000);

    } catch (error) {
      toast.error('Failed to send message');
    }
  };

  const handleEdit = (messageId: number) => {
    const message = messages.find(m => m.id === messageId);
    if (message) {
      setEditingId(messageId);
      setEditContent(message.content);
    }
  };

  const handleSaveEdit = async (messageId: number) => {
    try {
      // TODO: API call to edit message
      setMessages(prev =>
        prev.map(m =>
          m.id === messageId ? { ...m, content: editContent } : m
        ).filter(m => m.timestamp <= (messages.find(msg => msg.id === messageId)?.timestamp || ''))
      );
      
      setEditingId(null);
      setEditContent('');
      toast.success('Message edited successfully');
    } catch (error) {
      toast.error('Failed to edit message');
    }
  };

  const handleRegenerate = async (messageId: number) => {
    try {
      toast.info('Regenerating response...');
      
      // TODO: API call to regenerate
      setTimeout(() => {
        setMessages(prev =>
          prev.map(m =>
            m.id === messageId
              ? { ...m, content: 'Regenerated response: ' + m.content }
              : m
          )
        );
        toast.success('Response regenerated!');
      }, 1000);
      
    } catch (error) {
      toast.error('Failed to regenerate response');
    }
  };

  const handleBranch = async (messageId: number) => {
    try {
      toast.info('Creating conversation branch...');
      
      // TODO: API call to branch conversation
      setTimeout(() => {
        toast.success('Branch created! Opening in new tab...');
      }, 500);
      
    } catch (error) {
      toast.error('Failed to create branch');
    }
  };

  const handleExportMarkdown = async () => {
    try {
      // TODO: API call to export
      const markdown = messages
        .map(m => `### ${m.role === 'user' ? '🧑 User' : '🤖 Assistant'}\n\n${m.content}\n\n---\n`)
        .join('\n');

      const blob = new Blob([markdown], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat-${Date.now()}.md`;
      a.click();
      
      toast.success('Chat exported to Markdown!');
    } catch (error) {
      toast.error('Failed to export chat');
    }
  };

  const handleNewChat = () => {
    if (messages.length > 0 && !confirm('Start a new chat? Current conversation will be saved.')) {
      return;
    }
    setMessages([]);
    toast.info('Started new chat');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Enhanced Chat</h1>
          <p className="text-sm text-muted-foreground">
            With edit, regenerate, and branch features
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportMarkdown}
            className="px-3 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 flex items-center gap-2"
            title="Export to Markdown"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <button
            onClick={handleNewChat}
            className="px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            New Chat
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-12">
            <p>No messages yet. Start a conversation!</p>
            <p className="text-sm mt-2">Press Ctrl+Enter to send, Ctrl+N for new chat</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 p-4 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-50 dark:bg-blue-900/20'
                  : 'bg-secondary'
              }`}
            >
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
                {message.role === 'user' ? 'U' : 'A'}
              </div>

              <div className="flex-1">
                {editingId === message.id ? (
                  <div className="space-y-2">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg"
                      rows={3}
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSaveEdit(message.id)}
                        className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1 bg-secondary text-secondary-foreground rounded text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="prose dark:prose-invert max-w-none">
                      {message.content}
                    </div>
                    
                    <div className="flex gap-2 mt-2 text-sm">
                      <button
                        onClick={() => handleEdit(message.id)}
                        className="text-muted-foreground hover:text-foreground flex items-center gap-1"
                        title="Edit message"
                      >
                        <Edit2 className="w-3 h-3" />
                        Edit
                      </button>
                      
                      {message.role === 'assistant' && (
                        <button
                          onClick={() => handleRegenerate(message.id)}
                          className="text-muted-foreground hover:text-foreground flex items-center gap-1"
                          title="Regenerate response"
                        >
                          <RefreshCw className="w-3 h-3" />
                          Regenerate
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleBranch(message.id)}
                        className="text-muted-foreground hover:text-foreground flex items-center gap-1"
                        title="Branch conversation from here"
                      >
                        <GitBranch className="w-3 h-3" />
                        Branch
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type your message... (Ctrl+Enter to send)"
            className="flex-1 px-4 py-3 bg-background border border-border rounded-lg resize-none"
            rows={3}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Shortcuts: Ctrl+Enter (send), Ctrl+N (new chat)
        </p>
      </div>
    </div>
  );
}

