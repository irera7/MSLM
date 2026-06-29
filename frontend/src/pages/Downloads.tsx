import React, { useState, useEffect } from 'react'
import { downloadsApi } from '@/services/api'
import { useToast } from '@/components/ToastProvider'
import { Download, Pause, X, CheckCircle, AlertCircle, Loader2, FolderOpen } from 'lucide-react'

interface DownloadItem {
  id: number
  url: string
  destination: string
  model_name: string
  model_format: string
  status: 'pending' | 'downloading' | 'completed' | 'failed' | 'cancelled'
  progress: number
  downloaded_size: number
  total_size: number
  speed: number
  eta: number
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export default function Downloads() {
  const { toast } = useToast()
  const [downloads, setDownloads] = useState<DownloadItem[]>([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    loadDownloads()
    
    // Auto-refresh every 2 seconds if enabled
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadDownloads(true) // Silent refresh
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  const loadDownloads = async (silent = false) => {
    if (!silent) setLoading(true)
    
    try {
      const response = await downloadsApi.list()
      // Ensure downloads is always an array
      const data = response.data
      if (Array.isArray(data)) {
        setDownloads(data)
      } else if (data && Array.isArray(data.downloads)) {
        setDownloads(data.downloads)
      } else {
        setDownloads([])
      }
    } catch (error: any) {
      if (!silent) {
        console.error('Failed to load downloads:', error)
        toast.error('Failed to load downloads: ' + (error.response?.data?.detail || error.message))
      }
      setDownloads([])
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const handleCancel = async (id: number) => {
    try {
      await downloadsApi.cancel(id)
      toast.success('Download cancelled')
      loadDownloads()
    } catch (error: any) {
      toast.error('Failed to cancel download: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this download record?')) return
    
    try {
      await downloadsApi.delete(id)
      toast.success('Download deleted')
      loadDownloads()
    } catch (error: any) {
      toast.error('Failed to delete download: ' + (error.response?.data?.detail || error.message))
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatSpeed = (bytesPerSecond: number) => {
    return formatBytes(bytesPerSecond) + '/s'
  }

  const formatETA = (seconds: number) => {
    if (seconds <= 0) return 'Calculating...'
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    return `${Math.round(seconds / 3600)}h`
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      case 'cancelled':
        return <X className="w-5 h-5 text-gray-500" />
      default:
        return <Download className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
      case 'cancelled':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300'
      default:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
    }
  }

  const activeDownloads = downloads.filter(d => d.status === 'downloading' || d.status === 'pending')
  const completedDownloads = downloads.filter(d => d.status === 'completed')
  const failedDownloads = downloads.filter(d => d.status === 'failed' || d.status === 'cancelled')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-12 h-12 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Downloads</h1>
          <p className="text-muted-foreground mt-2">
            Track your model downloads
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-refresh
          </label>
          
          <button
            onClick={() => loadDownloads()}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Download className="w-8 h-8 text-blue-500" />
            <div>
              <p className="text-sm text-muted-foreground">Total Downloads</p>
              <p className="text-2xl font-bold">{downloads.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <div>
              <p className="text-sm text-muted-foreground">Active</p>
              <p className="text-2xl font-bold">{activeDownloads.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-green-500" />
            <div>
              <p className="text-sm text-muted-foreground">Completed</p>
              <p className="text-2xl font-bold">{completedDownloads.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-8 h-8 text-red-500" />
            <div>
              <p className="text-sm text-muted-foreground">Failed</p>
              <p className="text-2xl font-bold">{failedDownloads.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Active Downloads */}
      {activeDownloads.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Active Downloads</h2>
          <div className="space-y-4">
            {activeDownloads.map((download) => (
              <div key={download.id} className="bg-card border border-border rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3 flex-1">
                    {getStatusIcon(download.status)}
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{download.model_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {download.model_format} • {formatBytes(download.downloaded_size)} / {formatBytes(download.total_size)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(download.status)}`}>
                      {download.status}
                    </span>
                    
                    {(download.status === 'downloading' || download.status === 'pending') && (
                      <button
                        onClick={() => handleCancel(download.id)}
                        className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 dark:bg-red-900/30"
                        title="Cancel download"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-3">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-muted-foreground">{download.progress}%</span>
                    <span className="text-muted-foreground">
                      {download.speed > 0 && `${formatSpeed(download.speed)} • ETA: ${formatETA(download.eta)}`}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${download.progress}%` }}
                    />
                  </div>
                </div>

                <p className="text-sm text-muted-foreground font-mono truncate">
                  📁 {download.destination}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completed Downloads */}
      {completedDownloads.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Completed Downloads</h2>
          <div className="space-y-3">
            {completedDownloads.map((download) => (
              <div key={download.id} className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    {getStatusIcon(download.status)}
                    <div className="flex-1">
                      <h3 className="font-semibold">{download.model_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {download.model_format} • {formatBytes(download.total_size)}
                      </p>
                      <p className="text-xs text-muted-foreground font-mono mt-1">
                        📁 {download.destination}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(download.status)}`}>
                      ✓ Completed
                    </span>
                    <button
                      onClick={() => handleDelete(download.id)}
                      className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 dark:bg-gray-800"
                      title="Delete record"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Failed Downloads */}
      {failedDownloads.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Failed / Cancelled Downloads</h2>
          <div className="space-y-3">
            {failedDownloads.map((download) => (
              <div key={download.id} className="bg-card border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    {getStatusIcon(download.status)}
                    <div className="flex-1">
                      <h3 className="font-semibold">{download.model_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {download.model_format}
                      </p>
                      {download.error_message && (
                        <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                          Error: {download.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(download.status)}`}>
                      {download.status}
                    </span>
                    <button
                      onClick={() => handleDelete(download.id)}
                      className="p-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 dark:bg-gray-800"
                      title="Delete record"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {downloads.length === 0 && (
        <div className="text-center py-12">
          <Download className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No downloads yet</h3>
          <p className="text-muted-foreground mb-4">
            Start downloading models from the HuggingFace browser
          </p>
          <a
            href="/huggingface"
            className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            Browse HuggingFace Models
          </a>
        </div>
      )}

      {/* Info Panel */}
      <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
          💡 Download Information
        </h3>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• Downloaded models are automatically added to the Models page</li>
          <li>• Progress updates every 2 seconds (toggle auto-refresh off to pause)</li>
          <li>• You can cancel active downloads at any time</li>
          <li>• Completed downloads can be deleted from history</li>
          <li>• Download location: models/ directory in project root</li>
        </ul>
      </div>
    </div>
  )
}

