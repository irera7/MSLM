import { useState, useEffect } from 'react';
import { Play, Pause, CheckCircle, XCircle, Clock } from 'lucide-react';

interface BatchJob {
  job_id: string;
  status: string;
  total: number;
  completed: number;
  failed: number;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export default function BatchProcessor() {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [prompts, setPrompts] = useState('');
  const [modelId, setModelId] = useState('1');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      const response = await fetch('http://localhost:8078/api/batch/jobs');
      const data = await response.json();
      setJobs(data.jobs || []);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    }
  };

  const createJob = async () => {
    const promptList = prompts.split('\n').filter(p => p.trim());
    
    if (promptList.length === 0) {
      alert('Please enter at least one prompt');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8078/api/batch/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: parseInt(modelId),
          prompts: promptList,
          config: {
            temperature: 0.7,
            max_tokens: 512
          }
        })
      });

      if (response.ok) {
        setPrompts('');
        loadJobs();
        alert('Batch job created successfully');
      } else {
        alert('Failed to create batch job');
      }
    } catch (error) {
      console.error('Failed to create job:', error);
      alert('Failed to create batch job');
    }
    setLoading(false);
  };

  const cancelJob = async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8078/api/batch/jobs/${jobId}/cancel`, {
        method: 'POST'
      });

      if (response.ok) {
        loadJobs();
      }
    } catch (error) {
      console.error('Failed to cancel job:', error);
    }
  };

  const viewResults = async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8078/api/batch/jobs/${jobId}/results`);
      const data = await response.json();
      
      // Open in new window or download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (error) {
      console.error('Failed to get results:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'processing':
        return <Play className="w-5 h-5 text-blue-600" />;
      case 'cancelled':
        return <Pause className="w-5 h-5 text-gray-600" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-600" />;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Batch Processor</h1>
        <p className="text-muted-foreground mt-2">
          Process multiple prompts in batch
        </p>
      </div>

      {/* Create Batch Job */}
      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Create Batch Job</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Model ID
            </label>
            <input
              type="number"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Prompts (one per line)
            </label>
            <textarea
              value={prompts}
              onChange={(e) => setPrompts(e.target.value)}
              placeholder="Write a poem about AI&#10;Explain quantum computing&#10;Tell me a joke"
              rows={6}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg font-mono text-sm"
            />
            <p className="text-sm text-muted-foreground mt-1">
              {prompts.split('\n').filter(p => p.trim()).length} prompts
            </p>
          </div>

          <button
            onClick={createJob}
            disabled={loading}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Batch Job'}
          </button>
        </div>
      </div>

      {/* Jobs List */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Batch Jobs</h3>
        </div>

        <div className="divide-y divide-border">
          {jobs.map((job) => (
            <div key={job.job_id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <div className="font-medium">Job {job.job_id}</div>
                    <div className="text-sm text-muted-foreground">
                      {job.total} prompts • {job.completed} completed • {job.failed} failed
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  {job.status === 'completed' && (
                    <button
                      onClick={() => viewResults(job.job_id)}
                      className="px-3 py-1 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90"
                    >
                      View Results
                    </button>
                  )}
                  {job.status === 'processing' && (
                    <button
                      onClick={() => cancelJob(job.job_id)}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium">{job.progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>

              {/* Timestamps */}
              <div className="mt-4 text-sm text-muted-foreground">
                <div>Created: {new Date(job.created_at).toLocaleString()}</div>
                {job.started_at && (
                  <div>Started: {new Date(job.started_at).toLocaleString()}</div>
                )}
                {job.completed_at && (
                  <div>Completed: {new Date(job.completed_at).toLocaleString()}</div>
                )}
              </div>
            </div>
          ))}

          {jobs.length === 0 && (
            <div className="p-12 text-center text-muted-foreground">
              No batch jobs yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

