import React, { useState, useEffect } from 'react'
import { multimodalApi, modelsApi } from '../services/api'
import { useToast } from '../components/ToastProvider'

interface Model {
  id: number
  name: string
  format: string
}

export default function MultiModalManager() {
  const { toast } = useToast()
  const [models, setModels] = useState<Model[]>([])
  const [selectedModel, setSelectedModel] = useState<number>(0)
  const [loading, setLoading] = useState(false)
  const [supportedFormats, setSupportedFormats] = useState<{image: string[], audio: string[]}>({
    image: [],
    audio: []
  })

  // Vision
  const [visionPrompt, setVisionPrompt] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string>('')
  const [visionResponse, setVisionResponse] = useState('')

  // Audio
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [transcription, setTranscription] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [modelsRes, formatsRes] = await Promise.all([
        modelsApi.list(),
        multimodalApi.getFormats()
      ])
      
      setModels(modelsRes.data || [])
      setSupportedFormats(formatsRes.data)
      
      if (modelsRes.data && modelsRes.data.length > 0) {
        setSelectedModel(modelsRes.data[0].id)
      }
    } catch (error: any) {
      toast.error('Failed to load data: ' + error.message)
    }
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setImageFile(file)
      
      // Create preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleVisionGenerate = async () => {
    if (!imageFile || !visionPrompt) {
      toast.error('Please provide both image and prompt')
      return
    }

    setLoading(true)
    setVisionResponse('')

    try {
      // Convert image to base64
      const reader = new FileReader()
      reader.onloadend = async () => {
        const base64 = reader.result as string
        
        const response = await multimodalApi.visionGenerate(
          selectedModel,
          visionPrompt,
          undefined,
          base64
        )
        
        setVisionResponse(response.data.response)
        toast.success('Vision analysis complete!')
      }
      reader.readAsDataURL(imageFile)
    } catch (error: any) {
      toast.error('Vision generation failed: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAudioChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setAudioFile(file)
    }
  }

  const handleAudioTranscribe = async () => {
    if (!audioFile) {
      toast.error('Please provide an audio file')
      return
    }

    setLoading(true)
    setTranscription('')

    try {
      // Convert audio to base64
      const reader = new FileReader()
      reader.onloadend = async () => {
        const base64 = reader.result as string
        
        const response = await multimodalApi.audioTranscribe(
          selectedModel,
          undefined,
          base64
        )
        
        setTranscription(response.data.text)
        toast.success('Transcription complete!')
      }
      reader.readAsDataURL(audioFile)
    } catch (error: any) {
      toast.error('Transcription failed: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Multi-Modal AI
        </h1>
        <p className="text-gray-600">
          Process images and audio with AI models
        </p>
      </div>

      {/* Model Selection */}
      <div className="mb-6 bg-white rounded-lg shadow-md p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Model
        </label>
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(parseInt(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
        >
          {models.length === 0 ? (
            <option>No models available</option>
          ) : (
            models.map(model => (
              <option key={model.id} value={model.id}>
                {model.name} ({model.format})
              </option>
            ))
          )}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vision Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            🖼️ Vision (Image Understanding)
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Image
              </label>
              <input
                type="file"
                accept={supportedFormats.image.map(f => `.${f}`).join(',')}
                onChange={handleImageChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
              <p className="text-xs text-gray-500 mt-1">
                Supported: {supportedFormats.image.join(', ').toUpperCase()}
              </p>
            </div>

            {imagePreview && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Preview:</p>
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-full max-h-64 object-contain bg-gray-100 rounded-lg"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Prompt
              </label>
              <textarea
                value={visionPrompt}
                onChange={(e) => setVisionPrompt(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                rows={3}
                placeholder="What's in this image? Describe it in detail..."
              />
            </div>

            <button
              onClick={handleVisionGenerate}
              disabled={loading || !imageFile || !visionPrompt}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Analyzing...' : 'Analyze Image'}
            </button>

            {visionResponse && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Response:</p>
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-gray-800 whitespace-pre-wrap">
                    {visionResponse}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Audio Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            🎵 Audio (Speech-to-Text)
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Audio
              </label>
              <input
                type="file"
                accept={supportedFormats.audio.map(f => `.${f}`).join(',')}
                onChange={handleAudioChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
              <p className="text-xs text-gray-500 mt-1">
                Supported: {supportedFormats.audio.join(', ').toUpperCase()}
              </p>
            </div>

            {audioFile && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-700">
                  <strong>File:</strong> {audioFile.name}
                </p>
                <p className="text-sm text-gray-700">
                  <strong>Size:</strong> {(audioFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            )}

            <button
              onClick={handleAudioTranscribe}
              disabled={loading || !audioFile}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Transcribing...' : 'Transcribe Audio'}
            </button>

            {transcription && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Transcription:</p>
                <div className="p-4 bg-green-50 rounded-lg">
                  <p className="text-gray-800 whitespace-pre-wrap">
                    {transcription}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Example Use Cases */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-purple-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-purple-900 mb-3">
            🖼️ Vision Use Cases
          </h3>
          <ul className="space-y-2 text-sm text-purple-800">
            <li>• Image captioning and description</li>
            <li>• Visual question answering (VQA)</li>
            <li>• OCR (text extraction from images)</li>
            <li>• Image classification and tagging</li>
            <li>• Object detection and counting</li>
            <li>• Scene understanding</li>
          </ul>
        </div>

        <div className="bg-green-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-3">
            🎵 Audio Use Cases
          </h3>
          <ul className="space-y-2 text-sm text-green-800">
            <li>• Speech-to-text transcription</li>
            <li>• Voice command recognition</li>
            <li>• Audio content analysis</li>
            <li>• Language detection</li>
            <li>• Speaker identification</li>
            <li>• Audio accessibility features</li>
          </ul>
        </div>
      </div>

      {/* Info Panel */}
      <div className="mt-6 bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          💡 About Multi-Modal AI
        </h3>
        <div className="space-y-2 text-sm text-blue-800">
          <p>
            <strong>Multi-modal models</strong> can understand and process multiple types of data (images, audio, video, text) simultaneously.
          </p>
          <p>
            <strong>Vision Models:</strong> Use models like LLaVA, CLIP, BLIP for image understanding.
          </p>
          <p>
            <strong>Audio Models:</strong> Use models like Whisper for speech-to-text transcription.
          </p>
          <p>
            <strong>Note:</strong> This feature requires models specifically trained for multi-modal tasks.
          </p>
        </div>
      </div>
    </div>
  )
}

