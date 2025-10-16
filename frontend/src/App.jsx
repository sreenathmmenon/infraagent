import { useState, useEffect, useRef } from 'react'
import DemoControls from './components/DemoControls'
import { ToastContainer } from './components/Toast'

function App() {
  const [ws, setWs] = useState(null)
  const [toasts, setToasts] = useState([])
  const [infrastructureHealth, setInfrastructureHealth] = useState({
    healthy: 12,
    degraded: 2,
    critical: 0
  })

  // Active alerts awaiting approval
  const [pendingAlerts, setPendingAlerts] = useState([])

  // Active operations (currently executing)
  const [activeOperations, setActiveOperations] = useState([])

  // Recent completed activities (with rollback windows)
  const [recentActivities, setRecentActivities] = useState([])

  // Rollback progress tracking
  const [rollbackProgress, setRollbackProgress] = useState(null)
  const [rollbackStep, setRollbackStep] = useState(0)
  const rollbackProgressRef = useRef(null)

  // Runbooks
  const [runbooks, setRunbooks] = useState([])
  const [selectedRunbook, setSelectedRunbook] = useState(null)

  // Timer tick for countdown updates
  const [timerTick, setTimerTick] = useState(0)

  const addToast = (toast) => {
    const id = Date.now()
    setToasts(prev => [...prev, { ...toast, id }])
  }

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }

  useEffect(() => {
    // Don't load old activities from backend - they have expired rollback windows
    // Activities will be added dynamically as operations complete
    // fetchRecentActivities()

    // Fetch runbooks
    fetchRunbooks()
  }, [])

  const fetchRunbooks = async () => {
    try {
      const response = await fetch('/api/runbooks')
      const data = await response.json()
      setRunbooks(data.runbooks || [])
    } catch (error) {
      console.error('Error fetching runbooks:', error)
    }
  }

  const fetchRecentActivities = async () => {
    try {
      const response = await fetch('/api/activities?limit=3')
      const data = await response.json()
      setRecentActivities(data.activities || [])
    } catch (error) {
      console.error('Error fetching activities:', error)
    }
  }

  useEffect(() => {
    // WebSocket connection for real-time updates (non-blocking)
    let websocket
    let reconnectTimer

    const connectWebSocket = () => {
      try {
        websocket = new WebSocket('ws://localhost:8000/ws')

        websocket.onopen = () => {
          console.log('✅ WebSocket connected')
          setWs(websocket)
        }

        websocket.onmessage = (event) => {
          const data = JSON.parse(event.data)
          console.log('WebSocket message:', data)

      if (data.type === 'awaiting_approval') {
        // Add new alert to pending alerts
        const alertData = data.data.alert || {}
        const suggestionData = data.data.suggestion || {}

        // Extract duration from description (e.g., "for 5 minutes")
        const durationMatch = alertData.description?.match(/for (\d+\s+\w+)/i)
        const duration = durationMatch ? durationMatch[1] : 'N/A'

        const alert = {
          id: data.data.id,
          title: alertData.type?.replace(/_/g, ' ') || 'Infrastructure Alert',
          severity: alertData.severity?.toLowerCase() || 'critical',
          service: alertData.source || 'Unknown Service',
          metric: alertData.type?.replace(/_/g, ' ') || 'Unknown Metric',
          current_value: alertData.metric_value !== undefined ? `${alertData.metric_value}%` : 'N/A',
          threshold: alertData.threshold !== undefined ? `${alertData.threshold}%` : 'N/A',
          duration: duration,
          suggestion: {
            ...suggestionData,
            // Convert recommended_action object to string if needed
            recommended_action: typeof suggestionData.recommended_action === 'string'
              ? suggestionData.recommended_action
              : suggestionData.recommended_action?.description || suggestionData.recommended_action?.title || 'Automated remediation available',
            risk_level: suggestionData.risk_assessment?.level || 'Low',
            confidence: suggestionData.confidence || 90
          },
          status: 'pending'
        }
        setPendingAlerts(prev => [...prev, alert])

        // Update infrastructure health
        setInfrastructureHealth(prev => ({
          ...prev,
          critical: prev.critical + 1
        }))
      } else if (data.type === 'executing') {
        // Already handled by optimistic update in handleApprove
        console.log('Execution confirmed by backend:', data)
      } else if (data.type === 'completed') {
        // Completion is now handled by timer-based fallback (prevents duplicates)
        console.log('✅ COMPLETED EVENT RECEIVED (handled by timer):', data)
      } else if (data.type === 'rejected') {
        // Remove from pending alerts
        setPendingAlerts(prev => prev.slice(1))

        // Update infrastructure health
        setInfrastructureHealth(prev => ({
          ...prev,
          critical: Math.max(0, prev.critical - 1)
        }))
      }
    }

        websocket.onerror = (error) => {
          console.warn('⚠️ WebSocket error (app will work without real-time updates):', error)
          // App continues to work without WebSocket
        }

        websocket.onclose = () => {
          console.log('WebSocket disconnected')
          // Optionally reconnect after delay
          reconnectTimer = setTimeout(connectWebSocket, 5000)
        }
      } catch (error) {
        console.warn('⚠️ WebSocket connection failed (app will work without real-time updates):', error)
      }
    }

    // Initial connection attempt
    connectWebSocket()

    const heartbeat = setInterval(() => {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send('ping')
      }
    }, 30000)

    return () => {
      clearInterval(heartbeat)
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (websocket) websocket.close()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Update active operations step progression
  useEffect(() => {
    if (activeOperations.length > 0) {
      const operation = activeOperations[0]

      // Progress through steps up to last step (displays 1/6 to 6/6)
      if (operation.status === 'executing' && operation.currentStep < operation.totalSteps - 1) {
        const timer = setTimeout(() => {
          setActiveOperations(prev => {
            if (!prev[0]) return prev
            const updated = [...prev]
            updated[0] = { ...updated[0], currentStep: updated[0].currentStep + 1 }
            return updated
          })
        }, 2000) // 2 seconds per step

        return () => clearTimeout(timer)
      }
      // When last step is reached, fetch latest activity and complete
      else if (operation.status === 'executing' && operation.currentStep === operation.totalSteps - 1) {
        const completeTimer = setTimeout(async () => {
          try {
            // Fetch latest activity from backend
            const response = await fetch('/api/activities?limit=1')
            const data = await response.json()

            if (data.activities && data.activities.length > 0) {
              const latestActivity = data.activities[0]

              // Move to recent activities
              setActiveOperations(prev => prev.slice(1))

              setRecentActivities(prev => {
                // Only add if not already present
                if (!prev.find(a => a.id === latestActivity.id)) {
                  return [latestActivity, ...prev.slice(0, 4)]
                }
                return prev
              })

              setInfrastructureHealth(prev => ({
                ...prev,
                critical: Math.max(0, prev.critical - 1),
                healthy: prev.healthy + 1
              }))
            }
          } catch (error) {
            console.error('Error completing execution:', error)
          }
        }, 3000) // 3 seconds on last step, then complete

        return () => clearTimeout(completeTimer)
      }
    }
  }, [activeOperations])

  // Timer tick to update countdown displays every second
  useEffect(() => {
    const interval = setInterval(() => {
      setTimerTick(prev => prev + 1)
    }, 1000) // Update every second

    return () => clearInterval(interval)
  }, [])

  // Rollback step progression (5 seconds per step)
  useEffect(() => {
    if (!rollbackProgress) return

    const steps = rollbackProgress.rollback?.rollback_steps || []

    if (rollbackStep < steps.length) {
      const timer = setTimeout(() => {
        setRollbackStep(prev => prev + 1)
      }, 3000) // 3 seconds per rollback step

      return () => clearTimeout(timer)
    } else if (rollbackStep === steps.length && rollbackStep > 0) {
      // Rollback complete - call API (only once)
      const completeRollback = async () => {
        try {
          const response = await fetch(`/api/activities/${rollbackProgress.id}/rollback`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ performed_by: 'ops-user' })
          })

          if (response.ok) {
            addToast({
              type: 'success',
              title: 'Rollback Complete',
              message: 'All changes have been reverted successfully',
              duration: 5000
            })

            // Update the activity status to rolled_back
            setRecentActivities(prev => prev.map(a =>
              a.id === rollbackProgress.id
                ? {
                    ...a,
                    status: 'rolled_back',
                    rollback: { ...a.rollback, eligible: false, reason: 'Already rolled back' }
                  }
                : a
            ))

            setRollbackProgress(null)
            setRollbackStep(0)
          } else {
            const error = await response.json()
            addToast({
              type: 'error',
              title: 'Rollback Failed',
              message: error.detail || 'Failed to complete rollback',
              duration: 5000
            })
            setRollbackProgress(null)
            setRollbackStep(0)
          }
        } catch (error) {
          console.error('Error completing rollback:', error)
          addToast({
            type: 'error',
            title: 'Rollback Error',
            message: 'An error occurred during rollback',
            duration: 5000
          })
          setRollbackProgress(null)
          setRollbackStep(0)
        }
      }
      completeRollback()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rollbackProgress, rollbackStep])

  // Auto-scroll to rollback progress section when it appears
  useEffect(() => {
    if (rollbackProgress && rollbackProgressRef.current) {
      rollbackProgressRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      })
    }
  }, [rollbackProgress])

  const handleApprove = async (alertId) => {
    try {
      // Optimistic update - immediately move to active operations
      const alert = pendingAlerts.find(a => a.id === alertId)
      if (!alert) return

      // Remove from pending
      setPendingAlerts(prev => prev.filter(a => a.id !== alertId))

      // Add to active operations
      setActiveOperations(prev => [...prev, {
        ...alert,
        status: 'executing',
        currentStep: 0,
        totalSteps: 6,
        startTime: Date.now()
      }])

      // Call backend API
      const response = await fetch(`/api/approvals/${alertId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ approved_by: 'ops-user' })
      })

      if (!response.ok) {
        // Rollback optimistic update on error
        setActiveOperations(prev => prev.filter(op => op.id !== alertId))
        setPendingAlerts(prev => [...prev, alert])

        addToast({
          type: 'error',
          title: 'Approval Failed',
          message: 'Failed to approve remediation',
          duration: 5000
        })
      }
    } catch (error) {
      console.error('Error approving:', error)
      addToast({
        type: 'error',
        title: 'Approval Failed',
        message: 'Failed to approve remediation',
        duration: 5000
      })
    }
  }

  const handleReject = async (alertId) => {
    try {
      // Optimistic update - immediately remove from pending
      const alert = pendingAlerts.find(a => a.id === alertId)
      if (!alert) return

      setPendingAlerts(prev => prev.filter(a => a.id !== alertId))

      // Update infrastructure health
      setInfrastructureHealth(prev => ({
        ...prev,
        critical: Math.max(0, prev.critical - 1)
      }))

      addToast({
        type: 'info',
        title: 'Action Rejected',
        message: 'No changes were made to infrastructure',
        duration: 3000
      })

      // Call backend API
      const response = await fetch(`/api/approvals/${alertId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          reason: 'Rejected by operator',
          rejected_by: 'ops-user'
        })
      })

      if (!response.ok) {
        // Rollback on error
        setPendingAlerts(prev => [...prev, alert])
        setInfrastructureHealth(prev => ({
          ...prev,
          critical: prev.critical + 1
        }))
        addToast({
          type: 'error',
          title: 'Rejection Failed',
          message: 'Failed to reject action',
          duration: 5000
        })
      }
    } catch (error) {
      console.error('Error rejecting:', error)
    }
  }

  const handleRollback = (activityId) => {
    const activity = recentActivities.find(a => a.id === activityId)
    if (activity) {
      setRollbackProgress(activity)
      setRollbackStep(0)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-50 border-red-300 text-red-800'
      case 'warning': return 'bg-yellow-50 border-yellow-300 text-yellow-800'
      case 'info': return 'bg-blue-50 border-blue-300 text-blue-800'
      default: return 'bg-gray-50 border-gray-300 text-gray-800'
    }
  }

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'critical': return <span className="px-2 py-1 bg-red-500 text-white text-xs font-bold rounded-full">CRITICAL</span>
      case 'warning': return <span className="px-2 py-1 bg-yellow-500 text-white text-xs font-bold rounded-full">WARNING</span>
      case 'info': return <span className="px-2 py-1 bg-blue-500 text-white text-xs font-bold rounded-full">INFO</span>
      default: return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">InfraAgent</h1>
              <p className="text-slate-400 text-sm">Autonomous Infrastructure Operations</p>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-xs text-slate-400 uppercase tracking-wider">Last Check</div>
                <div className="text-white font-semibold">2 min ago</div>
              </div>
              <div className="h-8 w-px bg-slate-700"></div>
              <div className="text-right">
                <div className="text-xs text-slate-400 uppercase tracking-wider">Status</div>
                <div className="text-green-400 font-semibold flex items-center">
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                  Monitoring
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard */}
      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Infrastructure Overview */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Infrastructure Overview</h2>
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-green-300">Healthy</span>
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              </div>
              <div className="text-3xl font-bold text-white">{infrastructureHealth.healthy}</div>
              <div className="text-xs text-green-400 mt-1">Operating normally</div>
            </div>
            <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 border border-yellow-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-yellow-300">Degraded</span>
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              </div>
              <div className="text-3xl font-bold text-white">{infrastructureHealth.degraded}</div>
              <div className="text-xs text-yellow-400 mt-1">Performance issues</div>
            </div>
            <div className="bg-gradient-to-br from-red-500/10 to-red-600/10 border border-red-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-red-300">Critical</span>
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              </div>
              <div className="text-3xl font-bold text-white">{infrastructureHealth.critical}</div>
              <div className="text-xs text-red-400 mt-1">Requires attention</div>
            </div>
            <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-blue-300">Auto-Remediated</span>
                <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="text-3xl font-bold text-white">{recentActivities.length}</div>
              <div className="text-xs text-blue-400 mt-1">Last 24 hours</div>
            </div>
          </div>
        </div>

        {/* Infrastructure Services Breakdown */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Infrastructure Services</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Web Tier */}
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                  <span className="font-semibold text-white">Web Tier</span>
                </div>
                <span className="text-xs text-green-400 font-medium">✓ 3/3</span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-web-01</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-web-02</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-web-03</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
              </div>
            </div>

            {/* Database Tier */}
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                  </svg>
                  <span className="font-semibold text-white">Databases</span>
                </div>
                <span className="text-xs text-green-400 font-medium">✓ 2/2</span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-db-01 (Primary)</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-db-02 (Replica)</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
              </div>
            </div>

            {/* Message Queue */}
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                  <span className="font-semibold text-white">Message Queue</span>
                </div>
                <span className="text-xs text-yellow-400 font-medium">⚠ 1/2</span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-rabbitmq-01</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-rabbitmq-02</span>
                  <span className="text-yellow-400 text-xs">●</span>
                </div>
              </div>
            </div>

            {/* Cache Layer */}
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="font-semibold text-white">Cache Layer</span>
                </div>
                <span className="text-xs text-green-400 font-medium">✓ 2/2</span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-redis-01</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-redis-02</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
              </div>
            </div>

            {/* API Gateway */}
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="font-semibold text-white">API Gateway</span>
                </div>
                <span className="text-xs text-green-400 font-medium">✓ 2/2</span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-api-gateway-01</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-api-gateway-02</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
              </div>
            </div>

            {/* Kubernetes */}
            <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <span className="font-semibold text-white">Kubernetes</span>
                </div>
                <span className="text-xs text-green-400 font-medium">✓ 3/3</span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-k8s-node-01</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-k8s-node-02</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-300">prod-k8s-node-03</span>
                  <span className="text-green-400 text-xs">●</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Pending Approvals */}
        {pendingAlerts.length > 0 && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Pending Approval</h2>
              <span className="px-3 py-1 bg-orange-500/20 text-orange-300 text-sm font-semibold rounded-full border border-orange-500/30">
                {pendingAlerts.length} alert{pendingAlerts.length !== 1 ? 's' : ''}
              </span>
            </div>

            <div className="space-y-4">
              {pendingAlerts.map((alert) => (
                <div key={alert.id} className={`border-2 rounded-lg p-5 ${getSeverityColor(alert.severity)}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {getSeverityBadge(alert.severity)}
                        <span className="text-sm font-mono bg-black/20 px-2 py-0.5 rounded">{alert.service}</span>
                      </div>
                      <h3 className="text-lg font-bold mb-1">{alert.metric}</h3>
                      <div className="flex items-center gap-4 text-sm opacity-80">
                        <span>Current: <strong>{alert.current_value}</strong></span>
                        <span>Threshold: <strong>{alert.threshold}</strong></span>
                        <span>Duration: <strong>{alert.duration}</strong></span>
                      </div>
                    </div>
                  </div>

                  {alert.suggestion && (
                    <div className="mt-4 bg-white/70 backdrop-blur-sm rounded-lg p-4 border-2 border-white/50">
                      <div className="text-sm font-semibold text-gray-700 mb-2">Suggested Remediation</div>
                      <div className="text-sm text-gray-800 mb-3">
                        {typeof alert.suggestion.recommended_action === 'string'
                          ? alert.suggestion.recommended_action
                          : 'Automated remediation available'}
                      </div>
                      <div className="flex items-center gap-6 text-xs text-gray-700">
                        <span>Impact: <strong className="text-green-700">{alert.suggestion.risk_level || 'Low'}</strong></span>
                        <span>Success Rate: <strong className="text-blue-700">{alert.suggestion.confidence || 90}%</strong></span>
                        <span>ETA: <strong className="text-purple-700">~45s</strong></span>
                      </div>
                    </div>
                  )}

                  <div className="mt-4 flex items-center gap-3">
                    <button
                      onClick={() => handleApprove(alert.id)}
                      className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg"
                    >
                      ✓ Approve & Execute
                    </button>
                    <button
                      onClick={() => handleReject(alert.id)}
                      className="px-6 py-3 bg-white/80 text-gray-700 rounded-lg font-semibold hover:bg-white transition-all border-2 border-gray-300"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Active Operations */}
        {activeOperations.length > 0 && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Active Operations</h2>

            <div className="space-y-4">
              {activeOperations.map((operation) => (
                <div key={operation.id} className="bg-gradient-to-r from-blue-600/20 to-indigo-600/20 border-2 border-blue-500/40 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
                      <h3 className="text-lg font-bold text-white">Executing: {operation.service}</h3>
                    </div>
                    <div className="text-sm text-blue-300 font-mono">
                      Step {operation.currentStep + 1}/{operation.totalSteps}
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-xs text-blue-300 mb-2">
                      <span>Progress</span>
                      <span>{Math.round((operation.currentStep / operation.totalSteps) * 100)}%</span>
                    </div>
                    <div className="h-2 bg-blue-900/50 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-1000"
                        style={{ width: `${(operation.currentStep / operation.totalSteps) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Execution Steps */}
                  <div className="space-y-2">
                    {[
                      'Backing up current configuration',
                      'Analyzing resource patterns',
                      'Calculating optimal settings',
                      'Applying configuration changes',
                      'Reloading affected services',
                      'Validating changes & monitoring'
                    ].map((stepName, idx) => (
                      <div
                        key={idx}
                        className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                          idx < operation.currentStep
                            ? 'bg-green-500/20 border border-green-500/40'
                            : idx === operation.currentStep
                            ? 'bg-blue-500/30 border border-blue-500/60 animate-pulse'
                            : 'bg-slate-800/30 border border-slate-700/30 opacity-50'
                        }`}
                      >
                        {idx < operation.currentStep ? (
                          <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : idx === operation.currentStep ? (
                          <svg className="w-5 h-5 text-blue-400 flex-shrink-0 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        ) : (
                          <div className="w-5 h-5 border-2 border-slate-600 rounded-full flex-shrink-0"></div>
                        )}
                        <span className={`text-sm font-medium ${
                          idx <= operation.currentStep ? 'text-white' : 'text-slate-500'
                        }`}>
                          {stepName}
                        </span>
                        {idx === operation.currentStep && (
                          <span className="ml-auto text-xs text-blue-300 animate-pulse">Processing...</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Activity - ALWAYS VISIBLE */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Activity</h2>

          {recentActivities.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <p>No recent activities yet</p>
              <p className="text-sm mt-2">Complete a remediation to see rollback options here</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentActivities.map((activity) => {
                const now = new Date()
                const expiresAt = new Date(activity.rollback?.expires_at)
                const timeLeft = Math.max(0, Math.floor((expiresAt - now) / 1000))
                const minutes = Math.floor(timeLeft / 60)
                const seconds = timeLeft % 60
                const isRollbackAvailable = activity.rollback?.eligible && timeLeft > 0

                return (
                  <div key={activity.id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <h4 className="text-white font-semibold">{activity.title}</h4>
                          {activity.status === 'completed' && (
                            <span className="px-2 py-0.5 bg-green-500/20 text-green-300 text-xs font-medium rounded-full border border-green-500/30">
                              Completed
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-400 mb-2">{activity.description}</p>
                        <div className="text-xs text-slate-500">
                          {new Date(activity.timestamp).toLocaleTimeString()} • {activity.changes_made?.length || 0} changes
                        </div>
                      </div>

                      {isRollbackAvailable && (
                        <div className="ml-4 flex items-center gap-3">
                          <div className="text-right">
                            <div className="text-xs text-orange-400 font-semibold mb-1">⏱ UNDO AVAILABLE</div>
                            <div className="text-lg font-bold text-orange-300 font-mono">
                              {minutes}:{seconds.toString().padStart(2, '0')}
                            </div>
                          </div>
                          <button
                            onClick={() => handleRollback(activity.id)}
                            className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-lg transition-all shadow-lg"
                          >
                            Undo
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Rollback in Progress */}
        {rollbackProgress && (
          <div ref={rollbackProgressRef} className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">🔄 Rollback in Progress</h2>

            <div className="bg-gradient-to-r from-orange-600/20 to-red-600/20 border-2 border-orange-500/40 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-orange-400 rounded-full animate-pulse"></div>
                  <h3 className="text-lg font-bold text-white">Reverting: {rollbackProgress.title}</h3>
                </div>
                <div className="text-sm text-orange-300 font-mono">
                  Step {rollbackStep + 1}/{rollbackProgress.rollback?.rollback_steps?.length || 0}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-xs text-orange-300 mb-2">
                  <span>Rollback Progress</span>
                  <span>{Math.round((rollbackStep / (rollbackProgress.rollback?.rollback_steps?.length || 1)) * 100)}%</span>
                </div>
                <div className="h-2 bg-orange-900/50 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-orange-500 to-red-500 transition-all duration-1000"
                    style={{ width: `${(rollbackStep / (rollbackProgress.rollback?.rollback_steps?.length || 1)) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Rollback Steps in REVERSE */}
              <div className="space-y-2">
                {(rollbackProgress.rollback?.rollback_steps || []).map((stepName, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                      idx < rollbackStep
                        ? 'bg-green-500/20 border border-green-500/40'
                        : idx === rollbackStep
                        ? 'bg-orange-500/30 border border-orange-500/60 animate-pulse'
                        : 'bg-slate-800/30 border border-slate-700/30 opacity-50'
                    }`}
                  >
                    {idx < rollbackStep ? (
                      <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : idx === rollbackStep ? (
                      <svg className="w-5 h-5 text-orange-400 flex-shrink-0 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <div className="w-5 h-5 border-2 border-slate-600 rounded-full flex-shrink-0"></div>
                    )}
                    <span className={`text-sm font-medium ${
                      idx <= rollbackStep ? 'text-white' : 'text-slate-500'
                    }`}>
                      {stepName}
                    </span>
                    {idx === rollbackStep && (
                      <span className="ml-auto text-xs text-orange-300 animate-pulse">Reverting...</span>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-yellow-300">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span>Undoing changes - System will restore previous state</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Runbooks Library */}
        {runbooks.length > 0 && (
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  📚 Runbooks Library
                </h2>
                <p className="text-slate-400 text-sm mt-1">Automated remediation procedures for common infrastructure issues</p>
              </div>
              <span className="px-3 py-1 bg-blue-500/20 text-blue-300 text-sm font-semibold rounded-full border border-blue-500/30">
                {runbooks.length} runbooks
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {runbooks.map((runbook) => {
                const categoryColors = {
                  performance: 'bg-purple-50 border-purple-200 text-purple-800',
                  message_queue: 'bg-cyan-50 border-cyan-200 text-cyan-800',
                  storage: 'bg-orange-50 border-orange-200 text-orange-800',
                  deployment: 'bg-blue-50 border-blue-200 text-blue-800',
                  database: 'bg-indigo-50 border-indigo-200 text-indigo-800',
                  security: 'bg-red-50 border-red-200 text-red-800'
                }

                const severityColors = {
                  critical: 'bg-red-500',
                  high: 'bg-orange-500',
                  medium: 'bg-yellow-500',
                  low: 'bg-green-500'
                }

                const categoryColor = categoryColors[runbook.category] || 'bg-gray-50 border-gray-200 text-gray-800'
                const severityColor = severityColors[runbook.severity] || 'bg-gray-500'

                return (
                  <div
                    key={runbook.id}
                    className={`border-2 rounded-lg p-4 ${categoryColor} transition-all hover:shadow-lg cursor-pointer`}
                    onClick={() => setSelectedRunbook(selectedRunbook?.id === runbook.id ? null : runbook)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-bold text-base">{runbook.title}</h3>
                      <div className={`w-2 h-2 rounded-full ${severityColor}`} title={`${runbook.severity} severity`}></div>
                    </div>

                    <p className="text-sm opacity-75 mb-3 line-clamp-2">{runbook.description}</p>

                    <div className="flex items-center justify-between text-xs opacity-70">
                      <div className="flex items-center gap-2">
                        <span>⏱️ {runbook.estimated_duration}</span>
                        <span>•</span>
                        <span>✓ {runbook.success_rate}%</span>
                      </div>
                      <span>#{runbook.execution_count}</span>
                    </div>

                    {selectedRunbook?.id === runbook.id && (
                      <div className="mt-4 pt-4 border-t-2 border-opacity-20">
                        <div className="space-y-3">
                          <div>
                            <div className="text-xs font-bold uppercase tracking-wide mb-2">Steps ({runbook.steps.length})</div>
                            <div className="space-y-2">
                              {runbook.steps.map((step) => (
                                <div key={step.step} className="flex items-start gap-2 text-sm">
                                  <span className="font-semibold">{step.step}.</span>
                                  <div>
                                    <div className="font-medium">{step.name}</div>
                                    <div className="text-xs opacity-70">{step.estimated_time}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div>
                            <div className="text-xs font-bold uppercase tracking-wide mb-2">Risk Level</div>
                            <div className="text-sm">
                              <span className={`px-2 py-1 rounded ${severityColor} text-white font-medium`}>
                                {runbook.risk_assessment.risk_level.toUpperCase()}
                              </span>
                            </div>
                            <div className="text-xs mt-1 opacity-70">{runbook.risk_assessment.potential_impact}</div>
                          </div>

                          <div>
                            <div className="text-xs font-bold uppercase tracking-wide mb-2">Prerequisites</div>
                            <div className="space-y-1">
                              {runbook.prerequisites.map((prereq, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-xs">
                                  <span>•</span>
                                  <span>{prereq}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Empty State */}
        {pendingAlerts.length === 0 && activeOperations.length === 0 && recentActivities.length === 0 && !rollbackProgress && (
          <div className="text-center py-16">
            <div className="inline-block p-8 bg-slate-800/50 rounded-xl backdrop-blur-sm border border-slate-700">
              <svg className="w-16 h-16 text-slate-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-xl font-bold text-white mb-2">All Systems Operational</h3>
              <p className="text-slate-400 mb-4">No alerts or pending actions</p>
              <p className="text-sm text-slate-500">Use demo controls to simulate infrastructure alerts</p>
            </div>
          </div>
        )}
      </main>

      {/* Demo Controls */}
      <DemoControls />

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  )
}

export default App
