import React, { useState, useEffect } from 'react'
import { loraApi, modelsApi } from '../services/api'
import { useToast } from '../components/ToastProvider'

interface LoRAAdapter {
  name: string
  path: string
  base_model_id: number
  rank: number
  alpha: number
  scaling: number
  enabled: boolean
  target_modules: string[]
}

interface Model {
  id: number
  name: string
  format: string
  size: number
}

export default function LoRAManager() {
  const { toast } = useToast()
  const [adapters, setAdapters] = useState<LoRAAdapter[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  
  // Create adapter form
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm, setCreateForm] = useState({
    base_model_id: 0,
    adapter_name: '',
    rank: 8,
    alpha: 16,
    target_modules: 'q_proj,v_proj,k_proj,o_proj'
  })
  
  // Load adapter form
  const [showLoadForm, setShowLoadForm] = useState(false)
  const [loadForm, setLoadForm] = useState({
    adapter_path: '',
    base_model_id: 0,
    adapter_name: ''
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [adaptersRes, modelsRes] = await Promise.all([
        loraApi.list(),
        modelsApi.list()
      ])
      
      setAdapters(adaptersRes.data.adapters || [])
      setModels(modelsRes.data || [])
    } catch (error: any) {
      toast.error('Failed to load data: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAdapter = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const targetModules = createForm.target_modules.split(',').map(m => m.trim())
      
      await loraApi.create(
        createForm.base_model_id,
        createForm.adapter_name,
        createForm.rank,
        createForm.alpha,
        targetModules
      )
      
      toast.success(`Adapter '${createForm.adapter_name}' created successfully!`)
      setShowCreateForm(false)
      setCreateForm({
        base_model_id: 0,
        adapter_name: '',
        rank: 8,
        alpha: 16,
        target_modules: 'q_proj,v_proj,k_proj,o_proj'
      })
      loadData()
    } catch (error: any) {
      toast.error('Failed to create adapter: ' + error.message)
    }
  }

  const handleLoadAdapter = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await loraApi.load(
        loadForm.adapter_path,
        loadForm.base_model_id,
        loadForm.adapter_name
      )
      
      toast.success(`Adapter loaded successfully!`)
      setShowLoadForm(false)
      setLoadForm({
        adapter_path: '',
        base_model_id: 0,
        adapter_name: ''
      })
      loadData()
    } catch (error: any) {
      toast.error('Failed to load adapter: ' + error.message)
    }
  }

  const handleApplyAdapter = async (adapterName: string, modelId: number) => {
    try {
      await loraApi.apply(adapterName, modelId)
      toast.success(`Adapter '${adapterName}' applied to model!`)
      loadData()
    } catch (error: any) {
      toast.error('Failed to apply adapter: ' + error.message)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          LoRA Adapter Manager
        </h1>
        <p className="text-gray-600">
          Manage LoRA (Low-Rank Adaptation) adapters for efficient model fine-tuning
        </p>
      </div>

      {/* Action Buttons */}
      <div className="mb-6 flex gap-3">
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Create New Adapter
        </button>
        <button
          onClick={() => setShowLoadForm(true)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          📁 Load Existing Adapter
        </button>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Create Adapter Form */}
      {showCreateForm && (
        <div className="mb-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Create New LoRA Adapter</h2>
          <form onSubmit={handleCreateAdapter} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Adapter Name
              </label>
              <input
                type="text"
                value={createForm.adapter_name}
                onChange={(e) => setCreateForm({...createForm, adapter_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="my_custom_adapter"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base Model
              </label>
              <select
                value={createForm.base_model_id}
                onChange={(e) => setCreateForm({...createForm, base_model_id: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value={0}>Select a model...</option>
                {models.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.format})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rank (r)
                </label>
                <input
                  type="number"
                  value={createForm.rank}
                  onChange={(e) => setCreateForm({...createForm, rank: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  min="1"
                  max="256"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Lower = more efficient, less expressive (4, 8, 16, 32)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Alpha
                </label>
                <input
                  type="number"
                  value={createForm.alpha}
                  onChange={(e) => setCreateForm({...createForm, alpha: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  min="1"
                  max="512"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Scaling factor (typically 2x rank: 8, 16, 32)
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Modules (comma-separated)
              </label>
              <input
                type="text"
                value={createForm.target_modules}
                onChange={(e) => setCreateForm({...createForm, target_modules: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="q_proj,v_proj,k_proj,o_proj"
              />
              <p className="text-xs text-gray-500 mt-1">
                Which layers to adapt (default: attention layers)
              </p>
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Adapter
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Load Adapter Form */}
      {showLoadForm && (
        <div className="mb-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Load Existing LoRA Adapter</h2>
          <form onSubmit={handleLoadAdapter} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Adapter Path
              </label>
              <input
                type="text"
                value={loadForm.adapter_path}
                onChange={(e) => setLoadForm({...loadForm, adapter_path: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="/path/to/lora_adapter"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base Model
              </label>
              <select
                value={loadForm.base_model_id}
                onChange={(e) => setLoadForm({...loadForm, base_model_id: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value={0}>Select a model...</option>
                {models.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.format})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Adapter Name (optional)
              </label>
              <input
                type="text"
                value={loadForm.adapter_name}
                onChange={(e) => setLoadForm({...loadForm, adapter_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="Auto-detected from path"
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Load Adapter
              </button>
              <button
                type="button"
                onClick={() => setShowLoadForm(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Adapters List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">
          Loaded Adapters ({adapters.length})
        </h2>

        {adapters.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">No LoRA adapters loaded</p>
            <p className="text-sm">Create or load an adapter to get started</p>
          </div>
        ) : (
          <div className="space-y-4">
            {adapters.map((adapter, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {adapter.name}
                    </h3>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Base Model ID:</span>
                        <span className="ml-2 font-medium">{adapter.base_model_id}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Rank:</span>
                        <span className="ml-2 font-medium">{adapter.rank}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Alpha:</span>
                        <span className="ml-2 font-medium">{adapter.alpha}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Scaling:</span>
                        <span className="ml-2 font-medium">{adapter.scaling.toFixed(2)}</span>
                      </div>
                    </div>

                    <div className="mt-2">
                      <span className="text-sm text-gray-600">Target Modules:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {adapter.target_modules.map((module, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                          >
                            {module}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="mt-2 text-sm text-gray-500">
                      <span className="font-mono">{adapter.path}</span>
                    </div>
                  </div>

                  <div className="ml-4 flex flex-col gap-2">
                    <button
                      onClick={() => handleApplyAdapter(adapter.name, adapter.base_model_id)}
                      className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                    >
                      Apply
                    </button>
                    <span
                      className={`px-3 py-1 text-xs font-medium rounded ${
                        adapter.enabled
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {adapter.enabled ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Panel */}
      <div className="mt-6 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          💡 About LoRA
        </h3>
        <div className="space-y-2 text-sm text-blue-800">
          <p>
            <strong>LoRA (Low-Rank Adaptation)</strong> enables efficient fine-tuning by adding small trainable parameters to a frozen base model.
          </p>
          <p>
            <strong>Benefits:</strong> 10-100x less memory, faster training, smaller checkpoint sizes, easy to switch between tasks.
          </p>
          <p>
            <strong>Rank Guidelines:</strong> Small tasks (r=4), Medium tasks (r=8-16), Complex tasks (r=32-64)
          </p>
        </div>
      </div>
    </div>
  )
}

