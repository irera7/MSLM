import React, { useEffect, useState } from 'react'
import { 
  modelsApi, 
  chatApi, 
  monitoringApi, 
  downloadsApi,
  huggingfaceApi,
  ragApi,
  functionsApi,
  batchApi,
  apiKeysApi,
  quantizationApi,
  loraApi,
  multimodalApi,
  datasetsApi,
  pluginsApi,
  cacheApi
} from '../services/api'
import { useToast } from '../components/ToastProvider'

interface ServiceStatus {
  name: string
  status: 'checking' | 'online' | 'offline' | 'error'
  count?: number
  message?: string
}

export default function AdminDashboard() {
  const { toast } = useToast()
  const [services, setServices] = useState<ServiceStatus[]>([])
  const [systemInfo, setSystemInfo] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAllServices()
    loadSystemInfo()
  }, [])

  const checkAllServices = async () => {
    const serviceChecks: ServiceStatus[] = [
      { name: 'Models Service', status: 'checking' },
      { name: 'Chat Service', status: 'checking' },
      { name: 'Monitoring Service', status: 'checking' },
      { name: 'Downloads Service', status: 'checking' },
      { name: 'HuggingFace Service', status: 'checking' },
      { name: 'RAG Service', status: 'checking' },
      { name: 'Functions Service', status: 'checking' },
      { name: 'Batch Service', status: 'checking' },
      { name: 'API Keys Service', status: 'checking' },
      { name: 'Quantization Service', status: 'checking' },
      { name: 'LoRA Service', status: 'checking' },
      { name: 'Multi-Modal Service', status: 'checking' },
      { name: 'Datasets Service', status: 'checking' },
      { name: 'Plugins Service', status: 'checking' },
      { name: 'Cache Service', status: 'checking' },
    ]

    setServices(serviceChecks)

    // Check each service
    const checks = [
      checkService('Models Service', async () => {
        const res = await modelsApi.list()
        return { count: res.data.length || 0 }
      }),
      checkService('Chat Service', async () => {
        const res = await chatApi.listSessions()
        return { count: res.data.length || 0 }
      }),
      checkService('Monitoring Service', async () => {
        await monitoringApi.getSystemInfo()
        return {}
      }),
      checkService('Downloads Service', async () => {
        const res = await downloadsApi.list()
        return { count: res.data.length || 0 }
      }),
      checkService('HuggingFace Service', async () => {
        const res = await huggingfaceApi.getPopular(5)
        return { count: res.data.length || 0 }
      }),
      checkService('RAG Service', async () => {
        const res = await ragApi.getStatus()
        return { message: res.data.available ? 'Available' : 'Not Available' }
      }),
      checkService('Functions Service', async () => {
        const res = await functionsApi.list()
        return { count: res.data.functions?.length || 0 }
      }),
      checkService('Batch Service', async () => {
        const res = await batchApi.listJobs()
        return { count: res.data.jobs?.length || 0 }
      }),
      checkService('API Keys Service', async () => {
        const res = await apiKeysApi.list()
        return { count: res.data.length || 0 }
      }),
      checkService('Quantization Service', async () => {
        const res = await quantizationApi.listJobs()
        return { count: res.data.length || 0 }
      }),
      checkService('LoRA Service', async () => {
        const res = await loraApi.list()
        return { count: res.data.adapters?.length || 0 }
      }),
      checkService('Multi-Modal Service', async () => {
        const res = await multimodalApi.getFormats()
        return { message: 'Available' }
      }),
      checkService('Datasets Service', async () => {
        const res = await datasetsApi.list()
        return { count: res.data.datasets?.length || 0 }
      }),
      checkService('Plugins Service', async () => {
        const res = await pluginsApi.list()
        return { count: res.data.plugins?.length || 0 }
      }),
      checkService('Cache Service', async () => {
        const res = await cacheApi.getStats()
        return { message: `${res.data.size || 0} items` }
      }),
    ]

    const results = await Promise.allSettled(checks)

    const updatedServices = serviceChecks.map((service, index) => {
      const result = results[index]
      if (result.status === 'fulfilled') {
        return {
          ...service,
          ...result.value
        }
      } else {
        return {
          ...service,
          status: 'error' as const,
          message: 'Check failed'
        }
      }
    })

    setServices(updatedServices)
    setLoading(false)
  }

  const checkService = async (name: string, checkFn: () => Promise<any>) => {
    try {
      const result = await checkFn()
      return {
        name,
        status: 'online' as const,
        ...result
      }
    } catch (error) {
      return {
        name,
        status: 'offline' as const,
        message: 'Service unavailable'
      }
    }
  }

  const loadSystemInfo = async () => {
    try {
      const response = await monitoringApi.getSystemInfo()
      setSystemInfo(response.data)
    } catch (error) {
      console.error('Failed to load system info:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600'
      case 'offline': return 'text-red-600'
      case 'error': return 'text-yellow-600'
      default: return 'text-gray-400'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return '✓'
      case 'offline': return '✗'
      case 'error': return '⚠'
      default: return '○'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Checking all services...</p>
        </div>
      </div>
    )
  }

  const onlineCount = services.filter(s => s.status === 'online').length
  const totalCount = services.length

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Admin Dashboard
        </h1>
        <p className="text-gray-600">
          System overview and service status
        </p>
      </div>

      {/* Overall Status */}
      <div className="mb-8 bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">System Status</h2>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${onlineCount === totalCount ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
            <span className="text-sm font-medium">
              {onlineCount}/{totalCount} Services Online
            </span>
          </div>
        </div>

        {systemInfo && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-600">OS</p>
              <p className="text-lg font-semibold">{systemInfo.platform}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-600">Python</p>
              <p className="text-lg font-semibold">{systemInfo.python_version}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-600">CPU Cores</p>
              <p className="text-lg font-semibold">{systemInfo.cpu_count}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <p className="text-sm text-gray-600">Total RAM</p>
              <p className="text-lg font-semibold">
                {(systemInfo.total_ram / (1024**3)).toFixed(1)} GB
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((service, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md p-5 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-semibold text-gray-900">
                {service.name}
              </h3>
              <span className={`text-2xl ${getStatusColor(service.status)}`}>
                {getStatusIcon(service.status)}
              </span>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Status:</span>
                <span className={`font-medium ${getStatusColor(service.status)}`}>
                  {service.status === 'checking' ? 'Checking...' : service.status}
                </span>
              </div>

              {service.count !== undefined && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Items:</span>
                  <span className="font-medium text-gray-900">
                    {service.count}
                  </span>
                </div>
              )}

              {service.message && (
                <div className="text-sm text-gray-600 mt-2">
                  {service.message}
                </div>
              )}
            </div>

            {service.status === 'offline' && (
              <button
                onClick={() => checkAllServices()}
                className="mt-3 w-full px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Retry
              </button>
            )}
          </div>
        ))}
      </div>

      {/* API Endpoints Summary */}
      <div className="mt-8 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">API Endpoints</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="bg-blue-50 p-4 rounded">
            <p className="text-3xl font-bold text-blue-600">115+</p>
            <p className="text-sm text-gray-600 mt-1">Total Endpoints</p>
          </div>
          <div className="bg-green-50 p-4 rounded">
            <p className="text-3xl font-bold text-green-600">{onlineCount}</p>
            <p className="text-sm text-gray-600 mt-1">Services Online</p>
          </div>
          <div className="bg-purple-50 p-4 rounded">
            <p className="text-3xl font-bold text-purple-600">24</p>
            <p className="text-sm text-gray-600 mt-1">Total Services</p>
          </div>
          <div className="bg-orange-50 p-4 rounded">
            <p className="text-3xl font-bold text-orange-600">6</p>
            <p className="text-sm text-gray-600 mt-1">Inference Engines</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => checkAllServices()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Refresh Status
          </button>
          <button
            onClick={() => window.open('/api/docs', '_blank')}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            API Docs
          </button>
          <button
            onClick={() => cacheApi.clear()}
            className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
          >
            Clear Cache
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Reload Page
          </button>
        </div>
      </div>
    </div>
  )
}

