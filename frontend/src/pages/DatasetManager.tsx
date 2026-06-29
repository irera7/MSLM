import React, { useState, useEffect } from 'react'
import { datasetsApi } from '../services/api'
import { useToast } from '../components/ToastProvider'

interface Dataset {
  name: string
  type: string
  path: string
  num_samples: number
  format?: string
  description?: string
  created_at?: string
}

interface Sample {
  instruction?: string
  input?: string
  output?: string
  [key: string]: any
}

export default function DatasetManager() {
  const { toast } = useToast()
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null)
  const [samples, setSamples] = useState<Sample[]>([])
  const [showSamples, setShowSamples] = useState(false)
  
  // Create dataset form
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm, setCreateForm] = useState({
    name: '',
    dataset_type: 'instruction',
    description: ''
  })
  
  // Load dataset form
  const [showLoadForm, setShowLoadForm] = useState(false)
  const [loadForm, setLoadForm] = useState({
    path: '',
    format: 'jsonl',
    name: ''
  })

  // Add samples form
  const [showAddSamplesForm, setShowAddSamplesForm] = useState(false)
  const [newSample, setNewSample] = useState({
    instruction: '',
    input: '',
    output: ''
  })

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    setLoading(true)
    try {
      const response = await datasetsApi.list()
      setDatasets(response.data.datasets || [])
    } catch (error: any) {
      toast.error('Failed to load datasets: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateDataset = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await datasetsApi.create(
        createForm.name,
        createForm.dataset_type,
        createForm.description
      )
      
      toast.success(`Dataset '${createForm.name}' created successfully!`)
      setShowCreateForm(false)
      setCreateForm({ name: '', dataset_type: 'instruction', description: '' })
      loadDatasets()
    } catch (error: any) {
      toast.error('Failed to create dataset: ' + error.message)
    }
  }

  const handleLoadDataset = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await datasetsApi.load(
        loadForm.path,
        loadForm.format,
        loadForm.name
      )
      
      toast.success(`Dataset loaded successfully!`)
      setShowLoadForm(false)
      setLoadForm({ path: '', format: 'jsonl', name: '' })
      loadDatasets()
    } catch (error: any) {
      toast.error('Failed to load dataset: ' + error.message)
    }
  }

  const handleAddSample = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedDataset) return
    
    try {
      await datasetsApi.addSamples(selectedDataset, [newSample])
      
      toast.success('Sample added successfully!')
      setNewSample({ instruction: '', input: '', output: '' })
      setShowAddSamplesForm(false)
      
      // Refresh samples
      if (showSamples) {
        loadSamples(selectedDataset)
      }
      loadDatasets()
    } catch (error: any) {
      toast.error('Failed to add sample: ' + error.message)
    }
  }

  const loadSamples = async (datasetName: string) => {
    try {
      const response = await datasetsApi.getSamples(datasetName, 50, 0)
      setSamples(response.data.samples || [])
      setShowSamples(true)
    } catch (error: any) {
      toast.error('Failed to load samples: ' + error.message)
    }
  }

  const handleSplitDataset = async (datasetName: string) => {
    try {
      const response = await datasetsApi.split(datasetName, 0.8, 0.1, 0.1)
      toast.success(
        `Dataset split: Train=${response.data.train.size}, Val=${response.data.validation.size}, Test=${response.data.test.size}`
      )
    } catch (error: any) {
      toast.error('Failed to split dataset: ' + error.message)
    }
  }

  const handleExportDataset = async (datasetName: string) => {
    try {
      const outputPath = `/exports/${datasetName}.jsonl`
      await datasetsApi.export(datasetName, outputPath, 'jsonl')
      toast.success(`Dataset exported to ${outputPath}`)
    } catch (error: any) {
      toast.error('Failed to export dataset: ' + error.message)
    }
  }

  const handleDeleteDataset = async (datasetName: string) => {
    if (!confirm(`Are you sure you want to delete dataset '${datasetName}'?`)) {
      return
    }
    
    try {
      await datasetsApi.delete(datasetName)
      toast.success(`Dataset '${datasetName}' deleted`)
      if (selectedDataset === datasetName) {
        setSelectedDataset(null)
        setShowSamples(false)
      }
      loadDatasets()
    } catch (error: any) {
      toast.error('Failed to delete dataset: ' + error.message)
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
          Dataset Manager
        </h1>
        <p className="text-gray-600">
          Manage training datasets for model fine-tuning
        </p>
      </div>

      {/* Action Buttons */}
      <div className="mb-6 flex gap-3">
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Create Dataset
        </button>
        <button
          onClick={() => setShowLoadForm(true)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          📁 Load Dataset
        </button>
        <button
          onClick={loadDatasets}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Create Dataset Form */}
      {showCreateForm && (
        <div className="mb-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Create New Dataset</h2>
          <form onSubmit={handleCreateDataset} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dataset Name
              </label>
              <input
                type="text"
                value={createForm.name}
                onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="my_training_dataset"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dataset Type
              </label>
              <select
                value={createForm.dataset_type}
                onChange={(e) => setCreateForm({...createForm, dataset_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="instruction">Instruction Following</option>
                <option value="chat">Chat/Conversation</option>
                <option value="completion">Text Completion</option>
                <option value="classification">Classification</option>
                <option value="qa">Question Answering</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description (optional)
              </label>
              <textarea
                value={createForm.description}
                onChange={(e) => setCreateForm({...createForm, description: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                rows={3}
                placeholder="Brief description of the dataset..."
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create
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

      {/* Load Dataset Form */}
      {showLoadForm && (
        <div className="mb-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Load Existing Dataset</h2>
          <form onSubmit={handleLoadDataset} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                File Path
              </label>
              <input
                type="text"
                value={loadForm.path}
                onChange={(e) => setLoadForm({...loadForm, path: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="/path/to/dataset.jsonl"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Format
              </label>
              <select
                value={loadForm.format}
                onChange={(e) => setLoadForm({...loadForm, format: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="json">JSON</option>
                <option value="jsonl">JSONL</option>
                <option value="csv">CSV</option>
                <option value="parquet">Parquet</option>
                <option value="text">Plain Text</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dataset Name (optional)
              </label>
              <input
                type="text"
                value={loadForm.name}
                onChange={(e) => setLoadForm({...loadForm, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="Auto-detected from filename"
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Load
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

      {/* Datasets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {datasets.map((dataset, index) => (
          <div
            key={index}
            className={`bg-white rounded-lg shadow-md p-5 cursor-pointer transition-all ${
              selectedDataset === dataset.name
                ? 'ring-2 ring-blue-500'
                : 'hover:shadow-lg'
            }`}
            onClick={() => setSelectedDataset(dataset.name)}
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {dataset.name}
            </h3>
            
            <div className="space-y-1 text-sm mb-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium capitalize">{dataset.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Samples:</span>
                <span className="font-medium">{dataset.num_samples}</span>
              </div>
              {dataset.format && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Format:</span>
                  <span className="font-medium uppercase">{dataset.format}</span>
                </div>
              )}
            </div>

            {dataset.description && (
              <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                {dataset.description}
              </p>
            )}

            <div className="flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  loadSamples(dataset.name)
                }}
                className="flex-1 px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded hover:bg-blue-200"
              >
                View
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedDataset(dataset.name)
                  setShowAddSamplesForm(true)
                }}
                className="flex-1 px-3 py-1 bg-green-100 text-green-700 text-sm rounded hover:bg-green-200"
              >
                Add
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleSplitDataset(dataset.name)
                }}
                className="flex-1 px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded hover:bg-purple-200"
              >
                Split
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDeleteDataset(dataset.name)
                }}
                className="px-3 py-1 bg-red-100 text-red-700 text-sm rounded hover:bg-red-200"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>

      {datasets.length === 0 && (
        <div className="text-center py-12 text-gray-500 bg-white rounded-lg">
          <p className="text-lg mb-2">No datasets found</p>
          <p className="text-sm">Create or load a dataset to get started</p>
        </div>
      )}

      {/* Add Sample Form */}
      {showAddSamplesForm && selectedDataset && (
        <div className="mb-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">
            Add Sample to '{selectedDataset}'
          </h2>
          <form onSubmit={handleAddSample} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Instruction
              </label>
              <textarea
                value={newSample.instruction}
                onChange={(e) => setNewSample({...newSample, instruction: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                rows={2}
                placeholder="Write a poem about..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Input (optional)
              </label>
              <textarea
                value={newSample.input}
                onChange={(e) => setNewSample({...newSample, input: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                rows={2}
                placeholder="Additional context..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Output
              </label>
              <textarea
                value={newSample.output}
                onChange={(e) => setNewSample({...newSample, output: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                rows={4}
                placeholder="Expected model response..."
                required
              />
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Add Sample
              </button>
              <button
                type="button"
                onClick={() => setShowAddSamplesForm(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Samples Viewer */}
      {showSamples && samples.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              Samples from '{selectedDataset}' ({samples.length})
            </h2>
            <button
              onClick={() => setShowSamples(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕ Close
            </button>
          </div>

          <div className="space-y-4 max-h-[600px] overflow-y-auto">
            {samples.map((sample, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4"
              >
                <div className="text-sm font-medium text-gray-500 mb-2">
                  Sample #{index + 1}
                </div>
                
                {sample.instruction && (
                  <div className="mb-2">
                    <div className="text-xs font-semibold text-gray-600 uppercase mb-1">
                      Instruction:
                    </div>
                    <div className="text-sm text-gray-800 bg-blue-50 p-2 rounded">
                      {sample.instruction}
                    </div>
                  </div>
                )}

                {sample.input && (
                  <div className="mb-2">
                    <div className="text-xs font-semibold text-gray-600 uppercase mb-1">
                      Input:
                    </div>
                    <div className="text-sm text-gray-800 bg-yellow-50 p-2 rounded">
                      {sample.input}
                    </div>
                  </div>
                )}

                {sample.output && (
                  <div>
                    <div className="text-xs font-semibold text-gray-600 uppercase mb-1">
                      Output:
                    </div>
                    <div className="text-sm text-gray-800 bg-green-50 p-2 rounded">
                      {sample.output}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

