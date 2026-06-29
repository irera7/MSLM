import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi, modelsApi, multimodalApi } from '@/services/api'
import { ChatSession, ChatMessage } from '@/types'
import { Send, Plus, Loader2, Settings, Image, Mic, MicOff, FileText, X, Download } from 'lucide-react'
import { cn } from '@/lib/utils'
import jsPDF from 'jspdf'

export default function Chat() {
  const [selectedSession, setSelectedSession] = useState<number | null>(null)
  const [message, setMessage] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [streamedMessage, setStreamedMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  // Image support
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Voice support
  const [isRecording, setIsRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [audioChunks, setAudioChunks] = useState<Blob[]>([])
  const [isSpeaking, setIsSpeaking] = useState(false)

  // Search
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)

  const { data: sessions } = useQuery({
    queryKey: ['chat-sessions'],
    queryFn: () => chatApi.listSessions().then(res => res.data),
  })

  const { data: sessionData } = useQuery({
    queryKey: ['chat-session', selectedSession],
    queryFn: () => chatApi.getSession(selectedSession!).then(res => res.data),
    enabled: !!selectedSession,
  })

  const { data: loadedModels } = useQuery({
    queryKey: ['loaded-models'],
    queryFn: () => modelsApi.listLoaded().then(res => res.data),
  })

  const createSessionMutation = useMutation({
    mutationFn: (data: any) => chatApi.createSession(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
      setSelectedSession(response.data.id)
    },
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [sessionData?.messages, streamedMessage])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Ctrl+K: New Chat
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault()
        handleCreateSession()
      }
      // Ctrl+F: Search
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        setShowSearch(!showSearch)
      }
      // Ctrl+E: Export to PDF
      if (e.ctrlKey && e.key === 'e') {
        e.preventDefault()
        if (selectedSession) exportToPDF()
      }
      // Escape: Cancel actions
      if (e.key === 'Escape') {
        setShowSearch(false)
        removeImage()
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [selectedSession, showSearch])

  // Image handlers
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const removeImage = () => {
    setSelectedImage(null)
    setImagePreview('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // Voice input handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      
      recorder.ondataavailable = (e) => {
        setAudioChunks(prev => [...prev, e.data])
      }

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
        await transcribeAudio(audioBlob)
        setAudioChunks([])
        stream.getTracks().forEach(track => track.stop())
      }

      recorder.start()
      setMediaRecorder(recorder)
      setIsRecording(true)
    } catch (error) {
      console.error('Failed to start recording:', error)
      alert('Failed to access microphone')
    }
  }

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop()
      setIsRecording(false)
    }
  }

  const transcribeAudio = async (audioBlob: Blob) => {
    try {
      const reader = new FileReader()
      reader.onloadend = async () => {
        const base64Full = reader.result as string
        // Remove the data:audio/...;base64, prefix
        const base64Clean = base64Full.split(',')[1] || base64Full
        
        const models = await modelsApi.listLoaded()
        if (models.data.loaded_models.length > 0) {
          const response = await multimodalApi.audioTranscribe(
            models.data.loaded_models[0].model_id,
            undefined,
            base64Clean
          )
          setMessage(response.data.text)
        }
      }
      reader.readAsDataURL(audioBlob)
    } catch (error) {
      console.error('Transcription failed:', error)
    }
  }

  // Text-to-speech for responses
  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      window.speechSynthesis.speak(utterance)
    }
  }

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
    }
  }

  // PDF Export
  const exportToPDF = async () => {
    if (!sessionData) return

    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const margin = 20
    const maxWidth = pageWidth - 2 * margin
    let yPosition = 20

    // Title
    doc.setFontSize(16)
    doc.text(sessionData.name, margin, yPosition)
    yPosition += 10

    // Messages
    doc.setFontSize(10)
    sessionData.messages.forEach((msg: ChatMessage) => {
      const role = msg.role === 'user' ? 'You:' : 'AI:'
      const lines = doc.splitTextToSize(`${role} ${msg.content}`, maxWidth)
      
      lines.forEach((line: string) => {
        if (yPosition > 280) {
          doc.addPage()
          yPosition = 20
        }
        doc.text(line, margin, yPosition)
        yPosition += 7
      })
      yPosition += 5
    })

    doc.save(`${sessionData.name}.pdf`)
  }

  const handleSendMessage = async () => {
    if ((!message.trim() && !selectedImage) || !selectedSession || isGenerating) return

    const userMessage = message
    const imageToSend = selectedImage
    const imagePreviewToSend = imagePreview
    
    setMessage('')
    removeImage()
    setIsGenerating(true)
    setStreamedMessage('')

    try {
      // If image is attached, use multi-modal API
      if (imageToSend) {
        const reader = new FileReader()
        reader.onloadend = async () => {
          const base64Full = reader.result as string
          // Remove the data:image/...;base64, prefix
          const base64Clean = base64Full.split(',')[1] || base64Full
          
          const models = await modelsApi.listLoaded()
          if (models.data.loaded_models.length > 0) {
            const response = await multimodalApi.visionGenerate(
              models.data.loaded_models[0].model_id,
              userMessage,
              undefined,
              base64Clean
            )
            
            // Add messages to session
            await chatApi.addMessage(selectedSession, 'user', `${userMessage}\n[Image attached]`)
            await chatApi.addMessage(selectedSession, 'assistant', response.data.response)
            queryClient.invalidateQueries({ queryKey: ['chat-session', selectedSession] })
          }
        }
        reader.readAsDataURL(imageToSend)
        setIsGenerating(false)
        return
      }

      // Normal text generation
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8078/api'}/chat/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: selectedSession,
          message: userMessage,
          stream: true,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || 'Generation failed'
        throw new Error(errorMessage)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No reader')

      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue

            try {
              const parsed = JSON.parse(data)
              if (parsed.token) {
                accumulated += parsed.token
                setStreamedMessage(accumulated)
              }
              if (parsed.done) {
                break
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }

      // Refresh session to get the complete conversation
      queryClient.invalidateQueries({ queryKey: ['chat-session', selectedSession] })
    } catch (error: any) {
      console.error('Failed to generate:', error)
      const errorMsg = error.message || 'Failed to generate response'
      alert(errorMsg)
    } finally {
      setIsGenerating(false)
      setStreamedMessage('')
    }
  }

  const handleCreateSession = () => {
    if (!loadedModels || loadedModels.loaded_models.length === 0) {
      alert('Please load a model first')
      return
    }

    const modelId = loadedModels.loaded_models[0].model_id
    const name = prompt('Session name:', `Chat ${(sessions?.length || 0) + 1}`)

    if (name) {
      createSessionMutation.mutate({
        model_id: modelId,
        name,
        temperature: 0.7,
        top_p: 0.9,
        top_k: 40,
        max_tokens: 2048,
        repeat_penalty: 1.1,
        preset: 'Balanced',
      })
    }
  }

  // Mobile sidebar state
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  // Filter sessions by search
  const filteredSessions = sessions?.filter((session: ChatSession) =>
    session.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  return (
    <div className="flex h-full gap-4 relative">
      {/* Mobile menu button */}
      <button
        onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-primary text-primary-foreground rounded-lg shadow-lg"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Sessions Sidebar */}
      <div className={cn(
        "w-64 bg-card border border-border rounded-lg p-4 flex flex-col",
        "lg:relative lg:translate-x-0",
        "fixed inset-y-0 left-0 z-40 transition-transform duration-300",
        isMobileSidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Close button for mobile */}
        <button
          onClick={() => setIsMobileSidebarOpen(false)}
          className="lg:hidden absolute top-2 right-2 p-2"
        >
          <X className="w-4 h-4" />
        </button>
        <button
          onClick={handleCreateSession}
          className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 flex items-center justify-center gap-2 mb-4 mt-8 lg:mt-0"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">New Chat</span>
          <span className="sm:hidden">New</span>
        </button>

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div className="flex-1 overflow-auto space-y-2">
          {filteredSessions.length === 0 && searchQuery && (
            <p className="text-sm text-muted-foreground text-center py-4">
              No chats found
            </p>
          )}
          {filteredSessions.map((session: ChatSession) => (
            <button
              key={session.id}
              onClick={() => {
                setSelectedSession(session.id)
                setIsMobileSidebarOpen(false) // Close mobile sidebar on selection
              }}
              className={cn(
                'w-full text-left px-3 py-2 rounded-lg transition-colors',
                selectedSession === session.id
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-accent'
              )}
            >
              <p className="font-medium truncate">{session.name}</p>
              <p className="text-xs text-muted-foreground truncate">
                {session.preset}
              </p>
            </button>
          ))}
        </div>

        {/* Keyboard shortcuts hint */}
        <div className="mt-4 pt-4 border-t border-border hidden lg:block">
          <p className="text-xs text-muted-foreground mb-2">Shortcuts:</p>
          <div className="space-y-1 text-xs text-muted-foreground">
            <p>Ctrl+K: New Chat</p>
            <p>Ctrl+F: Search</p>
            <p>Ctrl+E: Export PDF</p>
          </div>
        </div>
      </div>

      {/* Mobile overlay */}
      {isMobileSidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsMobileSidebarOpen(false)}
        />
      )}

      {/* Chat Area */}
      <div className="flex-1 bg-card border border-border rounded-lg flex flex-col">
        {selectedSession && sessionData ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div>
                <h2 className="font-semibold">{sessionData.name}</h2>
                <p className="text-sm text-muted-foreground">
                  {sessionData.preset} • Temp: {sessionData.temperature}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={exportToPDF}
                  className="p-2 hover:bg-accent rounded-lg"
                  title="Export to PDF (Ctrl+E)"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button className="p-2 hover:bg-accent rounded-lg">
                  <Settings className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-auto p-4 space-y-4">
              {sessionData.messages.map((msg: ChatMessage) => (
                <div
                  key={msg.id}
                  className={cn(
                    'flex',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={cn(
                      'max-w-[70%] rounded-lg p-4',
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-accent'
                    )}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.role === 'assistant' && (
                      <button
                        onClick={() => isSpeaking ? stopSpeaking() : speakText(msg.content)}
                        className="mt-2 text-xs hover:underline"
                      >
                        {isSpeaking ? '🔊 Stop' : '🔉 Read aloud'}
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {/* Streaming message */}
              {isGenerating && streamedMessage && (
                <div className="flex justify-start">
                  <div className="max-w-[70%] rounded-lg p-4 bg-accent">
                    <p className="whitespace-pre-wrap">{streamedMessage}</p>
                    <Loader2 className="w-4 h-4 animate-spin mt-2" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Image Preview */}
            {imagePreview && (
              <div className="px-4 pb-2">
                <div className="relative inline-block">
                  <img
                    src={imagePreview}
                    alt="Selected"
                    className="max-h-32 rounded-lg border border-border"
                  />
                  <button
                    onClick={removeImage}
                    className="absolute -top-2 -right-2 p-1 bg-destructive text-destructive-foreground rounded-full"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Input */}
            <div className="p-4 border-t border-border">
              <div className="flex gap-2">
                {/* Image button */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 hover:bg-accent rounded-lg"
                  title="Attach image"
                >
                  <Image className="w-5 h-5" />
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="hidden"
                />

                {/* Voice button */}
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={cn(
                    'p-2 rounded-lg',
                    isRecording ? 'bg-red-500 text-white' : 'hover:bg-accent'
                  )}
                  title={isRecording ? 'Stop recording' : 'Voice input'}
                >
                  {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>

                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder={isRecording ? 'Recording...' : 'Type your message...'}
                  disabled={isGenerating || isRecording}
                  className="flex-1 px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={(!message.trim() && !selectedImage) || isGenerating}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
                >
                  {isGenerating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">No chat selected</p>
              <p className="text-sm">Create a new chat or select an existing one</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

