import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { modelsApi } from '@/services/api'
import { Model } from '@/types'
import { 
  Play, 
  Square, 
  Trash2, 
  Download,
  Database,
  Loader2,
  FileUp,
  Filter,
  Search,
  X
} from 'lucide-react'
import { formatBytes, formatDate, cn } from '@/lib/utils'
import Pagination from '@/components/Pagination'

export default function Models() {
  const navigate = useNavigate()
  const [formatFilter, setFormatFilter] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [showImportModal, setShowImportModal] = useState(false)
  const [importPath, setImportPath] = useState('')
  const [importName, setImportName] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(10)
  const queryClient = useQueryClient()

  const { data: modelsData, isLoading } = useQuery({
    queryKey: ['models', formatFilter, sourceFilter],
    queryFn: () => modelsApi.list({
      format_filter: formatFilter || undefined,
      source_filter: sourceFilter || undefined,
    }).then(res => {
      // Handle both response formats
      return res.data.models ? res.data : { models: res.data }
    }),
  })

  const loadMutation = useMutation({
    mutationFn: ({ id, gpu_layers }: { id: number; gpu_layers: number }) =>
      modelsApi.load(id, { gpu_layers, context_length: 2048 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      queryClient.invalidateQueries({ queryKey: ['loaded-models'] })
    },
  })

  const unloadMutation = useMutation({
    mutationFn: (id: number) => modelsApi.unload(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      queryClient.invalidateQueries({ queryKey: ['loaded-models'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => modelsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
    },
  })

  const importMutation = useMutation({
    mutationFn: ({ path, name }: { path: string; name: string }) =>
      modelsApi.import({ path, name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      setShowImportModal(false)
      setImportPath('')
      setImportName('')
      alert('Model imported successfully!')
    },
    onError: (error: any) => {
      alert('Failed to import model: ' + (error.response?.data?.detail || error.message))
    }
  })

  const handleLoad = (model: Model) => {
    const gpuLayers = window.confirm('Use GPU? (Click OK for GPU, Cancel for CPU)')
      ? -1
      : 0
    loadMutation.mutate({ id: model.id, gpu_layers: gpuLayers })
  }

  const handleImport = (e: React.FormEvent) => {
    e.preventDefault()
    if (!importPath || !importName) {
      alert('Please provide both path and name')
      return
    }
    importMutation.mutate({ path: importPath, name: importName })
  }

  // Filter models by search query
  const filteredModels = React.useMemo(() => {
    const models = Array.isArray(modelsData?.models) ? modelsData.models : []
    
    if (!searchQuery) return models
    
    const query = searchQuery.toLowerCase()
    return models.filter((model: Model) => {
      return (
        model.name?.toLowerCase().includes(query) ||
        model.format?.toLowerCase().includes(query) ||
        model.source?.toLowerCase().includes(query) ||
        model.quantization?.toLowerCase().includes(query) ||
        model.path?.toLowerCase().includes(query)
      )
    })
  }, [modelsData, searchQuery])

  // Pagination calculations
  const totalPages = Math.ceil(filteredModels.length / itemsPerPage)
  const paginatedModels = React.useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    return filteredModels.slice(startIndex, startIndex + itemsPerPage)
  }, [filteredModels, currentPage, itemsPerPage])

  // Reset to page 1 when filters change
  React.useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, formatFilter, sourceFilter])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Models</h1>
          <p className="text-muted-foreground mt-2">
            Manage your language models
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => navigate('/huggingface')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Browse HuggingFace
          </button>
          <button 
            onClick={() => setShowImportModal(true)}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 flex items-center gap-2"
          >
            <FileUp className="w-4 h-4" />
            Import Local
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search models by name, format, source..."
            className="w-full pl-10 pr-10 py-2 bg-card border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        
        <select
          value={formatFilter}
          onChange={(e) => setFormatFilter(e.target.value)}
          className="px-4 py-2 bg-card border border-border rounded-lg"
        >
          <option value="">All Formats</option>
          <option value="GGUF">GGUF</option>
          <option value="SAFETENSORS">SafeTensors</option>
          <option value="GPTQ">GPTQ</option>
          <option value="AWQ">AWQ</option>
          <option value="EXL2">EXL2</option>
          <option value="ONNX">ONNX</option>
        </select>

        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="px-4 py-2 bg-card border border-border rounded-lg"
        >
          <option value="">All Sources</option>
          <option value="HuggingFace">HuggingFace</option>
          <option value="Local">Local</option>
        </select>
      </div>

      {/* Results count */}
      {searchQuery && (
        <div className="text-sm text-muted-foreground">
          Found {filteredModels.length} model{filteredModels.length !== 1 ? 's' : ''} matching "{searchQuery}"
        </div>
      )}

      {/* Models List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : filteredModels.length > 0 ? (
        <>
          <div className="grid grid-cols-1 gap-4">
            {paginatedModels.map((model: Model) => (
            <div
              key={model.id}
              className={cn(
                'bg-card border rounded-lg p-6 transition-all',
                model.is_loaded ? 'border-primary' : 'border-border'
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <Database className="w-5 h-5 text-muted-foreground" />
                    <h3 className="text-lg font-semibold">{model.name}</h3>
                    {model.is_loaded && (
                      <span className="px-2 py-1 bg-green-500/10 text-green-500 text-xs rounded">
                        Loaded
                      </span>
                    )}
                  </div>

                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Format</p>
                      <p className="font-medium">{model.format}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Source</p>
                      <p className="font-medium">{model.source}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Size</p>
                      <p className="font-medium">
                        {model.size ? formatBytes(model.size) : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Quantization</p>
                      <p className="font-medium">{model.quantization || 'N/A'}</p>
                    </div>
                  </div>

                  <p className="mt-3 text-sm text-muted-foreground font-mono">{model.path}</p>
                </div>

                <div className="flex flex-col gap-2 ml-4">
                  {model.is_loaded ? (
                    <button
                      onClick={() => unloadMutation.mutate(model.id)}
                      disabled={unloadMutation.isPending}
                      className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 flex items-center gap-2 disabled:opacity-50"
                    >
                      <Square className="w-4 h-4" />
                      Unload
                    </button>
                  ) : (
                    <button
                      onClick={() => handleLoad(model)}
                      disabled={loadMutation.isPending}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 flex items-center gap-2 disabled:opacity-50"
                    >
                      <Play className="w-4 h-4" />
                      Load
                    </button>
                  )}

                  <button
                    onClick={() => {
                      if (window.confirm('Are you sure you want to delete this model?')) {
                        deleteMutation.mutate(model.id)
                      }
                    }}
                    disabled={deleteMutation.isPending}
                    className="px-4 py-2 bg-destructive/10 text-destructive rounded-lg hover:bg-destructive/20 flex items-center gap-2 disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Pagination */}
        {totalPages > 1 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            className="mt-6"
          />
        )}
      </>
      ) : (
        <div className="text-center py-12">
          <Database className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            {searchQuery ? `No models found matching "${searchQuery}"` : 'No models found'}
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Download a model from HuggingFace or import a local model to get started
          </p>
        </div>
      )}

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Import Local Model</h2>
              <button
                onClick={() => setShowImportModal(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleImport} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Model Path
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={importPath}
                    onChange={(e) => setImportPath(e.target.value)}
                    placeholder="D:\Project\modelServing\models\phi-2"
                    className="flex-1 px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    required
                  />
                  {/* File picker removed - web browsers can't access full file paths for security reasons */}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Enter the full path to your model directory or file. Example: D:\Project\modelServing\models\phi-2
                </p>
                <p className="text-xs text-yellow-600 dark:text-yellow-500 mt-1">
                  💡 Tip: Copy the full path from File Explorer (Shift + Right-click → "Copy as path")
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Model Name
                </label>
                <input
                  type="text"
                  value={importName}
                  onChange={(e) => setImportName(e.target.value)}
                  placeholder="Llama 2 7B"
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Display name for the model
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={importMutation.isPending}
                  className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                >
                  {importMutation.isPending ? 'Importing...' : 'Import'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowImportModal(false)}
                  className="flex-1 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90"
                >
                  Cancel
                </button>
              </div>
            </form>

            <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <p className="text-sm text-blue-400">
                💡 Tip: Make sure the model file exists and you have read permissions
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
