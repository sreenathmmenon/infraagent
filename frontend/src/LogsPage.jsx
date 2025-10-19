import { useState, useEffect } from 'react'

export default function LogsPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [services, setServices] = useState([])

  // Filters
  const [timeRange, setTimeRange] = useState('1h')
  const [selectedLevel, setSelectedLevel] = useState('ALL')
  const [selectedService, setSelectedService] = useState('ALL')
  const [searchText, setSearchText] = useState('')

  useEffect(() => {
    fetchLogs()
    fetchStats()
    fetchServices()

    // Refresh logs every 10 seconds
    const interval = setInterval(() => {
      fetchLogs()
      fetchStats()
    }, 10000)

    return () => clearInterval(interval)
  }, [timeRange, selectedLevel, selectedService, searchText])

  const fetchLogs = async () => {
    try {
      const queryParams = {
        limit: 100,
        offset: 0
      }

      // Add time filter
      if (timeRange !== 'ALL') {
        const hours = parseInt(timeRange)
        const now = Date.now() / 1000
        queryParams.start_time = now - (hours * 3600)
        queryParams.end_time = now
      }

      // Add level filter
      if (selectedLevel !== 'ALL') {
        queryParams.levels = [selectedLevel]
      }

      // Add service filter
      if (selectedService !== 'ALL') {
        queryParams.services = [selectedService]
      }

      // Add search
      if (searchText.trim()) {
        queryParams.search = searchText.trim()
      }

      const response = await fetch('/api/logs/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(queryParams)
      })

      if (response.ok) {
        const data = await response.json()
        setLogs(data.logs || [])
      }
    } catch (error) {
      console.error('Error fetching logs:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const hours = timeRange === 'ALL' ? 24 : parseInt(timeRange)
      const response = await fetch(`/api/logs/stats?hours=${hours}`)
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const fetchServices = async () => {
    try {
      const response = await fetch('/api/logs/services')
      if (response.ok) {
        const data = await response.json()
        setServices(data.services || [])
      }
    } catch (error) {
      console.error('Error fetching services:', error)
    }
  }

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR':
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-300 border-red-500/30'
      case 'WARN':
      case 'WARNING':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
      case 'INFO':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
      case 'DEBUG':
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
      default:
        return 'bg-gray-500/20 text-gray-300 border-gray-500/30'
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">🔍 Intelligent Log Analyzer</h1>
        <p className="text-slate-400">Real-time log streaming and analysis</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="max-w-7xl mx-auto grid grid-cols-5 gap-4 mb-6">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg border border-slate-700 p-4">
            <div className="text-slate-400 text-sm mb-1">Total Logs</div>
            <div className="text-2xl font-bold text-white">{stats.total}</div>
          </div>
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <div className="text-red-400 text-sm mb-1">Errors</div>
            <div className="text-2xl font-bold text-red-300">{stats.by_level?.ERROR || 0}</div>
          </div>
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <div className="text-yellow-400 text-sm mb-1">Warnings</div>
            <div className="text-2xl font-bold text-yellow-300">{stats.by_level?.WARN || 0}</div>
          </div>
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <div className="text-blue-400 text-sm mb-1">Info</div>
            <div className="text-2xl font-bold text-blue-300">{stats.by_level?.INFO || 0}</div>
          </div>
          <div className="bg-gray-500/10 border border-gray-500/30 rounded-lg p-4">
            <div className="text-gray-400 text-sm mb-1">Debug</div>
            <div className="text-2xl font-bold text-gray-300">{stats.by_level?.DEBUG || 0}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="max-w-7xl mx-auto bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-4 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Time Range */}
          <div>
            <label className="text-slate-400 text-sm mb-1 block">Time Range</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500"
            >
              <option value="1">Last Hour</option>
              <option value="6">Last 6 Hours</option>
              <option value="24">Last 24 Hours</option>
              <option value="ALL">All Time</option>
            </select>
          </div>

          {/* Level Filter */}
          <div>
            <label className="text-slate-400 text-sm mb-1 block">Level</label>
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Levels</option>
              <option value="ERROR">Errors</option>
              <option value="WARN">Warnings</option>
              <option value="INFO">Info</option>
              <option value="DEBUG">Debug</option>
            </select>
          </div>

          {/* Service Filter */}
          <div>
            <label className="text-slate-400 text-sm mb-1 block">Service</label>
            <select
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
              className="bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Services</option>
              {services.map(service => (
                <option key={service} value={service}>{service}</option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div className="flex-1">
            <label className="text-slate-400 text-sm mb-1 block">Search</label>
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Search logs..."
              className="w-full bg-slate-700 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Clear Filters */}
          <div className="self-end">
            <button
              onClick={() => {
                setTimeRange('1h')
                setSelectedLevel('ALL')
                setSelectedService('ALL')
                setSearchText('')
              }}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg border border-slate-600 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Logs List */}
      <div className="max-w-7xl mx-auto bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Log Stream</h2>
          <span className="text-slate-400 text-sm">
            Showing {logs.length} logs
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <p>No logs found matching your filters</p>
            <p className="text-sm mt-2">Try adjusting your time range or clearing filters</p>
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <div
                key={log.id}
                className={`border rounded-lg p-4 ${getLevelColor(log.level)} transition-all hover:border-opacity-70`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                      log.level === 'ERROR' ? 'bg-red-500' :
                      log.level === 'WARN' ? 'bg-yellow-500' :
                      log.level === 'INFO' ? 'bg-blue-500' :
                      'bg-gray-500'
                    } text-white`}>
                      {log.level}
                    </span>
                    <span className="text-sm font-mono bg-black/20 px-2 py-0.5 rounded text-slate-300">
                      {log.service}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      {formatTimestamp(log.timestamp)}
                    </span>
                  </div>
                </div>
                <p className="text-sm leading-relaxed">{log.message}</p>
                {log.metadata && Object.keys(log.metadata).length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-400">
                      Metadata
                    </summary>
                    <pre className="text-xs text-slate-400 mt-2 bg-black/20 p-2 rounded overflow-x-auto">
                      {JSON.stringify(log.metadata, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
