export interface Model {
  id: number
  name: string
  path: string
  format: string
  size?: number
  source: string
  source_url?: string
  quantization?: string
  parameters?: string
  metadata?: any
  is_loaded: boolean
  created_at: string
  updated_at: string
}

export interface ChatSession {
  id: number
  model_id: number
  name: string
  system_prompt?: string
  preset: string
  temperature: number
  top_p: number
  top_k: number
  max_tokens: number
  repeat_penalty: number
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: number
  session_id: number
  role: string
  content: string
  timestamp: string
  tokens?: number
}

export interface ChatSessionWithMessages extends ChatSession {
  messages: ChatMessage[]
}

export interface Download {
  id: number
  url: string
  destination?: string
  status: string
  progress: number
  model_name: string
  total_size?: number
  downloaded_size: number
  error_message?: string
  created_at: string
}

export interface LoadedModelInfo {
  model_id: number
  format: string
  context_length: number
  gpu_layers: number
  memory_usage_mb: number
}

