import { useState, useEffect } from 'react'

const ServiceCard = ({ service }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'critical':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getMetricColor = (value, thresholds = { warning: 80, critical: 90 }) => {
    if (value >= thresholds.critical) return 'text-red-400'
    if (value >= thresholds.warning) return 'text-yellow-400'
    return 'text-green-400'
  }

  return (
    <div className="bg-slate-700/30 rounded-lg p-3 border border-slate-600 hover:border-slate-500 transition-all">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center">
          <div className={`w-2 h-2 rounded-full ${getStatusColor(service.status)} mr-2`}></div>
          <div>
            <div className="text-sm font-semibold text-white">{service.name}</div>
            <div className="text-xs text-slate-400">{service.type}</div>
          </div>
        </div>
        {service.version && (
          <span className="text-xs text-slate-500 px-2 py-0.5 bg-slate-800 rounded">
            v{service.version}
          </span>
        )}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <div className="text-slate-400">CPU</div>
          <div className={`font-semibold ${getMetricColor(service.metrics.cpu_percent)}`}>
            {service.metrics.cpu_percent}%
          </div>
        </div>
        <div>
          <div className="text-slate-400">Memory</div>
          <div className={`font-semibold ${getMetricColor(service.metrics.memory_percent)}`}>
            {service.metrics.memory_percent}%
          </div>
        </div>
        <div>
          <div className="text-slate-400">Disk</div>
          <div className={`font-semibold ${getMetricColor(service.metrics.disk_percent)}`}>
            {service.metrics.disk_percent}%
          </div>
        </div>
      </div>

      {service.active_alert && (
        <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
          {service.active_alert}
        </div>
      )}

      {service.warning && (
        <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded text-xs text-yellow-400">
          {service.warning}
        </div>
      )}
    </div>
  )
}

const OverallHealth = ({ healthData }) => {
  const getHealthColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-400 border-green-400'
      case 'degraded':
        return 'text-yellow-400 border-yellow-400'
      case 'critical':
        return 'text-red-400 border-red-400'
      default:
        return 'text-gray-400 border-gray-400'
    }
  }

  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <div className={`border-2 rounded-lg p-4 ${getHealthColor(healthData.status)}`}>
        <div className="text-sm opacity-70 mb-1">Health Score</div>
        <div className="text-3xl font-bold">{healthData.score}</div>
        <div className="text-xs mt-1 capitalize">{healthData.status}</div>
      </div>

      <div className="border-2 border-green-400/30 rounded-lg p-4 text-green-400">
        <div className="text-sm opacity-70 mb-1">Healthy</div>
        <div className="text-3xl font-bold">{healthData.services_healthy}</div>
        <div className="text-xs mt-1">of {healthData.services_total} services</div>
      </div>

      <div className="border-2 border-yellow-400/30 rounded-lg p-4 text-yellow-400">
        <div className="text-sm opacity-70 mb-1">Degraded</div>
        <div className="text-3xl font-bold">{healthData.services_degraded || 0}</div>
        <div className="text-xs mt-1">needs attention</div>
      </div>

      <div className="border-2 border-red-400/30 rounded-lg p-4 text-red-400">
        <div className="text-sm opacity-70 mb-1">Critical</div>
        <div className="text-3xl font-bold">{healthData.services_critical || 0}</div>
        <div className="text-xs mt-1">active alerts</div>
      </div>
    </div>
  )
}

const CostSavings = ({ costData }) => {
  if (!costData || !costData.savings_opportunities) return null

  const totalSavings = costData.savings_opportunities.reduce(
    (sum, opp) => sum + opp.potential_monthly_savings_usd,
    0
  )

  return (
    <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-2 border-purple-400/30 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-white font-semibold">💰 Cost Optimization</h4>
        <div className="text-purple-400 text-sm">
          Save <span className="text-xl font-bold">${totalSavings}</span>/mo
        </div>
      </div>

      <div className="space-y-2">
        {costData.savings_opportunities.map((opp, idx) => (
          <div key={idx} className="flex items-start p-2 bg-slate-800/50 rounded text-sm">
            <svg className="w-4 h-4 text-purple-400 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <div className="flex-1">
              <div className="text-white font-medium">{opp.description}</div>
              <div className="text-purple-300 text-xs">${opp.potential_monthly_savings_usd}/mo savings</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const SecuritySummary = ({ securityData }) => {
  if (!securityData) return null

  const totalVulnerabilities =
    securityData.open_vulnerabilities.critical +
    securityData.open_vulnerabilities.high +
    securityData.open_vulnerabilities.medium +
    securityData.open_vulnerabilities.low

  return (
    <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-2 border-blue-400/30 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-white font-semibold">🔒 Security Status</h4>
        <div className="text-blue-400 text-sm">
          {totalVulnerabilities} vulnerabilities
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-800/50 rounded p-2">
          <div className="text-xs text-slate-400">Critical</div>
          <div className="text-2xl font-bold text-red-400">
            {securityData.open_vulnerabilities.critical}
          </div>
        </div>
        <div className="bg-slate-800/50 rounded p-2">
          <div className="text-xs text-slate-400">High</div>
          <div className="text-2xl font-bold text-orange-400">
            {securityData.open_vulnerabilities.high}
          </div>
        </div>
        <div className="bg-slate-800/50 rounded p-2">
          <div className="text-xs text-slate-400">Medium</div>
          <div className="text-2xl font-bold text-yellow-400">
            {securityData.open_vulnerabilities.medium}
          </div>
        </div>
        <div className="bg-slate-800/50 rounded p-2">
          <div className="text-xs text-slate-400">Low</div>
          <div className="text-2xl font-bold text-blue-400">
            {securityData.open_vulnerabilities.low}
          </div>
        </div>
      </div>

      <div className="mt-3 text-xs text-slate-400">
        Last scan: {new Date(securityData.last_security_scan).toLocaleString()}
      </div>
    </div>
  )
}

export default function HealthDashboard() {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboard()
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboard, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchDashboard = async () => {
    try {
      const response = await fetch('/api/health/dashboard')
      const data = await response.json()
      setDashboardData(data)
    } catch (error) {
      console.error('Error fetching dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">🏥 Infrastructure Health</h3>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
        </div>
      </div>
    )
  }

  if (!dashboardData) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Overall Health */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">🏥 Infrastructure Health</h3>
        <OverallHealth healthData={dashboardData.overall_health} />

        {/* Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {dashboardData.services.map((service) => (
            <ServiceCard key={service.id} service={service} />
          ))}
        </div>
      </div>

      {/* Cost & Security */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {dashboardData.cost_metrics && <CostSavings costData={dashboardData.cost_metrics} />}
        {dashboardData.security_summary && <SecuritySummary securityData={dashboardData.security_summary} />}
      </div>
    </div>
  )
}
