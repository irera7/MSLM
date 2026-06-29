import { useQuery } from '@tanstack/react-query'
import { modelsApi } from '@/services/api'
import { Database, Activity, Cpu, HardDrive } from 'lucide-react'

export default function Dashboard() {
  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: () => modelsApi.list().then(res => res.data),
  })

  const { data: loadedModels } = useQuery({
    queryKey: ['loaded-models'],
    queryFn: () => modelsApi.listLoaded().then(res => res.data),
    refetchInterval: 5000,
  })

  const stats = [
    {
      name: 'Total Models',
      value: modelsData?.total || 0,
      icon: Database,
      color: 'text-blue-500',
    },
    {
      name: 'Loaded Models',
      value: loadedModels?.count || 0,
      icon: Activity,
      color: 'text-green-500',
    },
    {
      name: 'Memory Usage',
      value: `${(loadedModels?.total_memory_mb || 0).toFixed(0)} MB`,
      icon: Cpu,
      color: 'text-orange-500',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Overview of your LM Studio Clone instance
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.name}</p>
                  <p className="text-3xl font-bold mt-2">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-lg bg-accent ${stat.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Loaded Models */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Loaded Models</h2>
        {loadedModels && loadedModels.loaded_models.length > 0 ? (
          <div className="space-y-3">
            {loadedModels.loaded_models.map((model: any) => (
              <div
                key={model.model_id}
                className="flex items-center justify-between p-4 bg-accent rounded-lg"
              >
                <div>
                  <p className="font-medium">Model ID: {model.model_id}</p>
                  <p className="text-sm text-muted-foreground">
                    {model.format} • {model.context_length} context • {model.gpu_layers} GPU layers
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">
                    {model.memory_usage_mb.toFixed(0)} MB
                  </p>
                  <p className="text-xs text-muted-foreground">Memory</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground text-center py-8">
            No models currently loaded
          </p>
        )}
      </div>
    </div>
  )
}

