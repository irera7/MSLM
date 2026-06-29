import { useState, useEffect } from 'react'
import { Search, Download, Loader2, ExternalLink, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { huggingfaceApi, downloadsApi } from '@/services/api'
import { useToast } from '@/components/ToastProvider'

interface HFModel {
  id: string
  author: string
  modelId: string
  downloads: number
  likes: number
  tags: string[]
  lastModified: string
}

export default function HuggingFaceBrowser() {
  const toast = useToast()  // ✅ بدون destructuring
  const navigate = useNavigate()
  const [models, setModels] = useState<HFModel[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterFormat, setFilterFormat] = useState('')

  useEffect(() => {
    loadPopularModels()
  }, [])

  const loadPopularModels = async () => {
    setLoading(true)
    try {
      const response = await huggingfaceApi.getPopular(20)
      setModels(response.data || [])
    } catch (error: any) {
      console.error('Failed to load models:', error)
      toast.error('Failed to load popular models: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const searchModels = async () => {
    if (!searchQuery.trim()) {
      loadPopularModels()
      return
    }

    setLoading(true)
    try {
      const response = await huggingfaceApi.search({
        query: searchQuery,
        limit: 20,
        filter: filterFormat || undefined
      })
      
      setModels(response.data || [])
      
      if (!response.data || response.data.length === 0) {
        toast.info(`No models found for "${searchQuery}"`)
      } else {
        toast.success(`Found ${response.data.length} models`)
      }
    } catch (error: any) {
      console.error('Failed to search models:', error)
      toast.error('Search failed: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const downloadModel = async (modelId: string) => {
    console.log('=== DOWNLOAD MODEL CALLED ===', modelId)
    
    // برای PyTorch/Transformers models، باید کل repo را download کنیم نه فقط یک فایل
    // پس مستقیم repo ID را به backend می‌فرستیم
    
    if (!confirm(
      `Download full model repository?\n\n` +
      `Model: ${modelId}\n\n` +
      `This will download all necessary files from HuggingFace.\n` +
      `Note: This may take several minutes depending on model size.`
    )) {
      console.log('User cancelled download')
      return
    }

    try {
      console.log('Starting model download...')
      
      const downloadRequest = {
        url: modelId,  // فقط model ID را می‌فرستیم
        model_name: modelId.split('/').pop() || modelId,
        model_format: 'PyTorch',  // Default format
        priority: 0,
        metadata: {
          hf_repo: modelId,
          source: 'huggingface',
          download_type: 'full_repo'  // نشان می‌دهد کل repo را می‌خواهیم
        }
      }
      
      console.log('Sending download request:', downloadRequest)
      
      const response = await downloadsApi.start(downloadRequest)
      console.log('Download response:', response)

      toast.success('Download started! This may take a while...')
      
      // Redirect to downloads page after 1 second
      setTimeout(() => {
        console.log('Redirecting to /downloads')
        navigate('/downloads')
      }, 1000)
    } catch (error: any) {
      console.error('=== DOWNLOAD ERROR ===')
      console.error('Error object:', error)
      console.error('Error response:', error.response)
      console.error('Error message:', error.message)
      toast.error('Failed to start download: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      searchModels()
    }
  }

  const clearSearch = () => {
    setSearchQuery('')
    setFilterFormat('')
    loadPopularModels()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">HuggingFace Model Browser</h1>
        <p className="text-muted-foreground mt-2">
          Browse and download models from HuggingFace Hub
        </p>
      </div>

      {/* Search Bar */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Search models (e.g., 'llama', 'mistral', 'gpt')..."
            className="w-full pl-10 pr-10 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {searchQuery && (
            <button
              onClick={clearSearch}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
              title="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <select
          value={filterFormat}
          onChange={(e) => setFilterFormat(e.target.value)}
          className="px-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="">All Formats</option>
          <option value="gguf">GGUF</option>
          <option value="safetensors">SafeTensors</option>
          <option value="pytorch">PyTorch</option>
        </select>

        <button
          onClick={searchModels}
          disabled={loading}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Search
            </>
          )}
        </button>
      </div>

      {/* Quick Search Suggestions */}
      {!searchQuery && (
        <div className="flex gap-2 flex-wrap">
          <span className="text-sm text-muted-foreground">Quick search:</span>
          {['llama', 'mistral', 'phi', 'gemma', 'qwen'].map((tag) => (
            <button
              key={tag}
              onClick={() => {
                setSearchQuery(tag)
                // Trigger search after state update
                setTimeout(() => searchModels(), 100)
              }}
              className="px-3 py-1 bg-secondary text-secondary-foreground text-sm rounded-lg hover:bg-secondary/80"
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {/* Results Count */}
      {!loading && models.length > 0 && (
        <div className="text-sm text-muted-foreground">
          {searchQuery ? (
            <>Found {models.length} model{models.length !== 1 ? 's' : ''} for "{searchQuery}"</>
          ) : (
            <>Showing {models.length} popular models</>
          )}
        </div>
      )}

      {/* Models Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground">
            {searchQuery ? `Searching for "${searchQuery}"...` : 'Loading popular models...'}
          </p>
        </div>
      ) : models.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.map((model) => (
            <div
              key={model.id}
              className="bg-card border border-border rounded-lg p-4 hover:shadow-lg transition-all hover:border-primary/50"
            >
              <div className="space-y-3">
                <div>
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-lg truncate flex-1">
                      {model.modelId || model.id}
                    </h3>
                    <a
                      href={`https://huggingface.co/${model.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-primary ml-2"
                      title="View on HuggingFace"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    by {model.author}
                  </p>
                </div>

                <div className="flex gap-4 text-sm text-muted-foreground">
                  <span title="Downloads">⬇️ {(model.downloads || 0).toLocaleString()}</span>
                  <span title="Likes">❤️ {(model.likes || 0).toLocaleString()}</span>
                </div>

                {model.tags && model.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {model.tags.slice(0, 4).map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded"
                        title={tag}
                      >
                        {tag}
                      </span>
                    ))}
                    {model.tags.length > 4 && (
                      <span className="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded">
                        +{model.tags.length - 4}
                      </span>
                    )}
                  </div>
                )}

                <button
                  onClick={() => downloadModel(model.id)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Search className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-lg text-muted-foreground mb-2">
            {searchQuery ? `No models found for "${searchQuery}"` : 'No models found'}
          </p>
          <p className="text-sm text-muted-foreground">
            Try a different search query or check your filters
          </p>
          {searchQuery && (
            <button
              onClick={clearSearch}
              className="mt-4 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90"
            >
              Clear Search
            </button>
          )}
        </div>
      )}

      {/* Info Panel */}
      <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
          💡 Search Tips
        </h3>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• Search by model name: "llama", "mistral", "gpt"</li>
          <li>• Filter by format to find specific model types</li>
          <li>• Press Enter to search quickly</li>
          <li>• Click model cards to view on HuggingFace</li>
        </ul>
      </div>
    </div>
  )
}
