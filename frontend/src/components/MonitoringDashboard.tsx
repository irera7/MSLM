import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface SystemInfo {
  platform: string;
  cpu_count: number;
  ram_total_gb: number;
  gpu_available: boolean;
  gpu_count: number;
}

interface Metrics {
  cpu: {
    percent: number;
  };
  ram: {
    used_gb: number;
    percent: number;
  };
}

export default function MonitoringDashboard() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSystemInfo();
    const interval = setInterval(loadMetrics, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemInfo = async () => {
    try {
      const response = await fetch('http://localhost:8078/api/monitoring/system');
      const data = await response.json();
      setSystemInfo(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load system info:', error);
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8078/api/monitoring/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading monitoring data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
        System Monitoring
      </h2>

      {/* System Info */}
      {systemInfo && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-200">
              System
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Platform: {systemInfo.platform}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              CPU Cores: {systemInfo.cpu_count}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              RAM: {systemInfo.ram_total_gb.toFixed(1)} GB
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-200">
              GPU
            </h3>
            {systemInfo.gpu_available ? (
              <>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Available: Yes
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Count: {systemInfo.gpu_count}
                </p>
              </>
            ) : (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                No GPU detected
              </p>
            )}
          </div>

          {metrics && (
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-200">
                Current Load
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                CPU: {metrics.cpu.percent.toFixed(1)}%
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                RAM: {metrics.ram.used_gb.toFixed(1)} GB ({metrics.ram.percent.toFixed(1)}%)
              </p>
            </div>
          )}
        </div>
      )}

      {/* Real-time Metrics */}
      {metrics && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-200">
            Real-time Metrics
          </h3>
          
          {/* CPU Usage Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600 dark:text-gray-400">CPU Usage</span>
              <span className="text-gray-600 dark:text-gray-400">
                {metrics.cpu.percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(metrics.cpu.percent, 100)}%` }}
              />
            </div>
          </div>

          {/* RAM Usage Bar */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600 dark:text-gray-400">RAM Usage</span>
              <span className="text-gray-600 dark:text-gray-400">
                {metrics.ram.percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(metrics.ram.percent, 100)}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

