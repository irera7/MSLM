import { Settings as SettingsIcon, Cpu, HardDrive, Zap } from 'lucide-react'

export default function Settings() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Configure your LM Studio Clone instance
        </p>
      </div>

      {/* Model Settings */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5" />
          Model Settings
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Max Concurrent Models
            </label>
            <input
              type="number"
              defaultValue={3}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            />
            <p className="text-sm text-muted-foreground mt-1">
              Maximum number of models that can be loaded simultaneously
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Default Context Length
            </label>
            <input
              type="number"
              defaultValue={2048}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            />
            <p className="text-sm text-muted-foreground mt-1">
              Default context window size for models
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Default GPU Layers
            </label>
            <select
              defaultValue="0"
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            >
              <option value="0">CPU Only</option>
              <option value="10">10 Layers</option>
              <option value="20">20 Layers</option>
              <option value="32">32 Layers</option>
              <option value="-1">All Layers (Full GPU)</option>
            </select>
            <p className="text-sm text-muted-foreground mt-1">
              Number of model layers to offload to GPU
            </p>
          </div>
        </div>
      </div>

      {/* Download Settings */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <HardDrive className="w-5 h-5" />
          Download Settings
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Max Concurrent Downloads
            </label>
            <input
              type="number"
              defaultValue={3}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            />
            <p className="text-sm text-muted-foreground mt-1">
              Maximum number of simultaneous downloads
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Models Directory
            </label>
            <input
              type="text"
              defaultValue="./models"
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            />
            <p className="text-sm text-muted-foreground mt-1">
              Directory where downloaded models are stored
            </p>
          </div>
        </div>
      </div>

      {/* Performance Settings */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5" />
          Performance
        </h2>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Enable Caching</p>
              <p className="text-sm text-muted-foreground">
                Cache responses for identical prompts
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Enable Monitoring</p>
              <p className="text-sm text-muted-foreground">
                Track system resource usage
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90">
          Save Settings
        </button>
      </div>
    </div>
  )
}

