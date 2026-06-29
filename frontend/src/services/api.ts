import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8078/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Models API
export const modelsApi = {
  list: (params?: { skip?: number; limit?: number; format_filter?: string; source_filter?: string }) =>
    api.get('/models/', { params }),  // با trailing slash
  
  get: (id: number) =>
    api.get(`/models/${id}`),
  
  create: (data: any) =>
    api.post('/models/', data),  // با trailing slash
  
  update: (id: number, data: any) =>
    api.patch(`/models/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/models/${id}`),
  
  load: (id: number, data?: { gpu_layers?: number; context_length?: number }) =>
    api.post(`/models/${id}/load`, { model_id: id, ...data }),
  
  unload: (id: number) =>
    api.post(`/models/${id}/unload`),
  
  listLoaded: () =>
    api.get('/models/loaded/list'),
  
  unloadAll: () =>
    api.post('/models/unload_all'),
  
  // Import & Detection
  import: (data: { path: string; name: string; format?: string }) =>
    api.post('/models/import', data),
  
  detectFormat: (path: string) =>
    api.post('/models/detect-format', { path }),
  
  // Versioning
  createVersion: (id: number, version: string, notes?: string) =>
    api.post(`/models/${id}/versions`, null, { params: { version, notes } }),
  
  listVersions: (id: number) =>
    api.get(`/models/${id}/versions`),
  
  // Comparison
  compare: (model_ids: number[]) =>
    api.post('/models/compare', { model_ids }),
  
  // Benchmarking
  benchmark: (id: number, num_prompts: number = 5) =>
    api.post(`/models/${id}/benchmark`, null, { params: { num_prompts } }),
  
  getBenchmark: (id: number) =>
    api.get(`/models/${id}/benchmark`),
  
  // Tagging
  addTags: (id: number, tags: string[]) =>
    api.post(`/models/${id}/tags`, tags),
  
  removeTags: (id: number, tags: string[]) =>
    api.delete(`/models/${id}/tags`, { data: tags }),
  
  setCategory: (id: number, category: string) =>
    api.post(`/models/${id}/category`, null, { params: { category } }),
  
  searchByTags: (tags: string, match_all: boolean = false) =>
    api.get('/models/search/tags', { params: { tags, match_all } }),
}

// Chat API
export const chatApi = {
  createSession: (data: any) =>
    api.post('/chat/sessions', data),
  
  listSessions: (params?: { model_id?: number; skip?: number; limit?: number }) =>
    api.get('/chat/sessions', { params }),
  
  getSession: (id: number) =>
    api.get(`/chat/sessions/${id}`),
  
  updateSession: (id: number, data: any) =>
    api.patch(`/chat/sessions/${id}`, data),
  
  deleteSession: (id: number) =>
    api.delete(`/chat/sessions/${id}`),
  
  generate: (data: { session_id: number; message: string; stream: boolean }) =>
    api.post('/chat/generate', data),
  
  exportSession: (id: number) =>
    api.get(`/chat/sessions/${id}/export`),
  
  exportMarkdown: (id: number) =>
    api.get(`/chat/sessions/${id}/export-markdown`),
  
  // Presets
  listPresets: () =>
    api.get('/chat/presets'),
  
  applyPreset: (id: number, preset_name: string) =>
    api.post(`/chat/sessions/${id}/apply-preset`, null, { params: { preset_name } }),
  
  // Message Operations
  editMessage: (message_id: number, content: string) =>
    api.patch(`/chat/messages/${message_id}`, { content }),
  
  regenerateMessage: (message_id: number, params?: { temperature?: number; max_tokens?: number }) =>
    api.post(`/chat/messages/${message_id}/regenerate`, params),
  
  branchConversation: (session_id: number, from_message_id?: number, new_name?: string) =>
    api.post(`/chat/sessions/${session_id}/branch`, { from_message_id, new_name }),
  
  addMessage: (session_id: number, role: string, content: string) =>
    api.post(`/chat/sessions/${session_id}/messages`, { role, content }),
}

// Downloads API
export const downloadsApi = {
  start: (data: any) =>
    api.post('/downloads/', data),  // با trailing slash
  
  list: (params?: { status_filter?: string; skip?: number; limit?: number }) =>
    api.get('/downloads/', { params }),  // با trailing slash
  
  getStatus: (id: number) =>
    api.get(`/downloads/${id}`),
  
  cancel: (id: number) =>
    api.post(`/downloads/${id}/cancel`),
  
  delete: (id: number) =>
    api.delete(`/downloads/${id}`),
  
  listActive: () =>
    api.get('/downloads/active/list'),
}

// Monitoring API
export const monitoringApi = {
  getSystemInfo: () =>
    api.get('/monitoring/system'),
  
  getMetrics: () =>
    api.get('/monitoring/metrics'),
  
  getMetricsHistory: (minutes: number = 60) =>
    api.get('/monitoring/metrics/history', { params: { minutes } }),
  
  getProcessInfo: () =>
    api.get('/monitoring/process'),
  
  getGPUInfo: () =>
    api.get('/monitoring/gpu'),
  
  clearHistory: () =>
    api.delete('/monitoring/metrics/history'),
}

// Cache API
export const cacheApi = {
  getStats: () =>
    api.get('/cache/stats'),
  
  clear: () =>
    api.delete('/cache/clear'),
  
  invalidateModel: (model_id: number) =>
    api.delete(`/cache/model/${model_id}`),
  
  cleanup: () =>
    api.post('/cache/cleanup'),
}

// HuggingFace API
export const huggingfaceApi = {
  search: (params: { query: string; limit?: number; filter?: string }) =>
    api.get('/huggingface/search', { params }),
  
  getModel: (model_id: string) =>
    api.get(`/huggingface/model/${model_id}`),
  
  getModelFiles: (model_id: string) =>
    api.get(`/huggingface/model/${model_id}/files`),
  
  getPopular: (limit: number = 20) =>
    api.get('/huggingface/popular', { params: { limit } }),
  
  getGGUF: (limit: number = 20) =>
    api.get('/huggingface/gguf', { params: { limit } }),
  
  getDownloadUrl: (model_id: string, file: string) =>
    api.get(`/huggingface/download-url/${model_id}/${file}`),
}

// RAG API
export const ragApi = {
  getStatus: () =>
    api.get('/rag/status'),
  
  createCollection: (name: string) =>
    api.post('/rag/collections', { name }),
  
  listCollections: () =>
    api.get('/rag/collections'),
  
  getCollection: (name: string) =>
    api.get(`/rag/collections/${name}`),
  
  deleteCollection: (name: string) =>
    api.delete(`/rag/collections/${name}`),
  
  addDocuments: (collection_name: string, documents: string[], metadatas?: any[]) =>
    api.post('/rag/documents', { collection_name, documents, metadatas }),
  
  query: (collection_name: string, query: string, n_results: number = 5) =>
    api.post('/rag/query', { collection_name, query, n_results }),
  
  buildPrompt: (collection_name: string, query: string, base_prompt: string) =>
    api.post('/rag/build-prompt', { collection_name, query, base_prompt }),
}

// Functions API
export const functionsApi = {
  list: () =>
    api.get('/functions/'),
  
  getSchema: () =>
    api.get('/functions/schema'),
  
  execute: (name: string, args: any) =>
    api.post('/functions/execute', { name, arguments: args }),
  
  parse: (text: string) =>
    api.post('/functions/parse', { text }),
  
  buildPrompt: (functions: any[], user_message: string) =>
    api.post('/functions/build-prompt', { functions, user_message }),
}

// Batch API
export const batchApi = {
  createJob: (model_id: number, prompts: string[], config?: any) =>
    api.post('/batch/jobs', { model_id, prompts, config }),
  
  listJobs: () =>
    api.get('/batch/jobs'),
  
  getStatus: (job_id: string) =>
    api.get(`/batch/jobs/${job_id}/status`),
  
  getResults: (job_id: string) =>
    api.get(`/batch/jobs/${job_id}/results`),
  
  cancel: (job_id: string) =>
    api.post(`/batch/jobs/${job_id}/cancel`),
  
  delete: (job_id: string) =>
    api.delete(`/batch/jobs/${job_id}`),
}

// API Keys
export const apiKeysApi = {
  create: (name: string, rate_limit?: number) =>
    api.post('/keys/', { name, rate_limit }),
  
  list: (include_inactive: boolean = false) =>
    api.get('/keys/', { params: { include_inactive } }),
  
  revoke: (key_id: number) =>
    api.delete(`/keys/${key_id}`),
  
  getUsage: (key_id: number, days: number = 7) =>
    api.get(`/keys/${key_id}/usage`, { params: { days } }),
}

// Quantization API
export const quantizationApi = {
  start: (model_id: number, output_name: string, quantization_level: string) =>
    api.post('/quantization/', { model_id, output_name, quantization_level }),
  
  getStatus: (job_id: string) =>
    api.get(`/quantization/${job_id}`),
  
  listJobs: () =>
    api.get('/quantization/'),
  
  getLevels: () =>
    api.get('/quantization/info/levels'),
}

// Advanced Features - LoRA
export const loraApi = {
  load: (adapter_path: string, base_model_id: number, adapter_name?: string) =>
    api.post('/advanced/lora/load', { adapter_path, base_model_id, adapter_name }),
  
  create: (base_model_id: number, adapter_name: string, rank?: number, alpha?: number, target_modules?: string[]) =>
    api.post('/advanced/lora/create', { base_model_id, adapter_name, rank, alpha, target_modules }),
  
  list: (model_id?: number) =>
    api.get('/advanced/lora/list', { params: { model_id } }),
  
  get: (adapter_name: string) =>
    api.get(`/advanced/lora/${adapter_name}`),
  
  apply: (adapter_name: string, model_id: number) =>
    api.post(`/advanced/lora/${adapter_name}/apply`, null, { params: { model_id } }),
}

// Advanced Features - Multi-Modal
export const multimodalApi = {
  visionGenerate: (model_id: number, prompt: string, image_path?: string, image_base64?: string, image_url?: string) =>
    api.post('/advanced/multimodal/vision/generate', { model_id, prompt, image_path, image_base64, image_url }),
  
  audioTranscribe: (model_id: number, audio_path?: string, audio_base64?: string) =>
    api.post('/advanced/multimodal/audio/transcribe', { model_id, audio_path, audio_base64 }),
  
  getCapabilities: (model_id: number) =>
    api.get(`/advanced/multimodal/capabilities/${model_id}`),
  
  getFormats: () =>
    api.get('/advanced/multimodal/formats'),
}

// Advanced Features - Datasets
export const datasetsApi = {
  create: (name: string, dataset_type: string, description?: string) =>
    api.post('/advanced/datasets/', { name, dataset_type, description }),
  
  load: (path: string, format: string, name?: string) =>
    api.post('/advanced/datasets/load', { path, format, name }),
  
  list: () =>
    api.get('/advanced/datasets/'),
  
  get: (dataset_name: string) =>
    api.get(`/advanced/datasets/${dataset_name}`),
  
  addSamples: (dataset_name: string, samples: any[]) =>
    api.post('/advanced/datasets/samples/add', { dataset_name, samples }),
  
  getSamples: (dataset_name: string, limit: number = 100, offset: number = 0) =>
    api.get(`/advanced/datasets/${dataset_name}/samples`, { params: { limit, offset } }),
  
  split: (dataset_name: string, train_ratio: number = 0.8, val_ratio: number = 0.1, test_ratio: number = 0.1) =>
    api.post(`/advanced/datasets/${dataset_name}/split`, null, { params: { train_ratio, val_ratio, test_ratio } }),
  
  delete: (dataset_name: string) =>
    api.delete(`/advanced/datasets/${dataset_name}`),
  
  export: (dataset_name: string, output_path: string, format: string) =>
    api.post(`/advanced/datasets/${dataset_name}/export`, null, { params: { output_path, format } }),
}

// Plugins API
export const pluginsApi = {
  list: () =>
    api.get('/plugins/'),
  
  get: (name: string) =>
    api.get(`/plugins/${name}`),
  
  load: (plugin_path: string) =>
    api.post('/plugins/load', { plugin_path }),
  
  reload: () =>
    api.post('/plugins/reload'),
  
  unload: (name: string) =>
    api.delete(`/plugins/${name}`),
}

export default api
