import { useState, useEffect } from 'react'
import RollbackModal from './RollbackModal'
import PostMortemModal from './PostMortemModal'

const ACTIVITY_ICONS = {
  alert_fix: '🚨',
  deployment: '🚀',
  config_change: '⚙️',
  disk_cleanup: '🗑️',
  message_queue_maintenance: '📬',
  security_patch: '🔒',
  database_tuning: '🗄️'
}

const ACTIVITY_COLORS = {
  alert_fix: 'bg-red-50 border-red-200 text-red-800',
  deployment: 'bg-blue-50 border-blue-200 text-blue-800',
  config_change: 'bg-purple-50 border-purple-200 text-purple-800',
  disk_cleanup: 'bg-orange-50 border-orange-200 text-orange-800',
  message_queue_maintenance: 'bg-cyan-50 border-cyan-200 text-cyan-800',
  security_patch: 'bg-green-50 border-green-200 text-green-800',
  database_tuning: 'bg-indigo-50 border-indigo-200 text-indigo-800'
}

const RollbackTimer = ({ expiresAt, activityId, onRollback }) => {
  const [timeLeft, setTimeLeft] = useState('')
  const [expired, setExpired] = useState(false)

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date()
      const expiry = new Date(expiresAt)
      const diff = expiry - now

      if (diff <= 0) {
        setExpired(true)
        setTimeLeft('Expired')
        return
      }

      const minutes = Math.floor(diff / 60000)
      const seconds = Math.floor((diff % 60000) / 1000)
      setTimeLeft(`${minutes}m ${seconds}s`)
    }

    updateTimer()
    const interval = setInterval(updateTimer, 1000)

    return () => clearInterval(interval)
  }, [expiresAt])

  if (expired) return null

  return (
    <div className="flex items-center justify-between mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
      <div className="flex items-center">
        <svg className="w-4 h-4 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm text-yellow-800 font-medium">
          Rollback available: {timeLeft}
        </span>
      </div>
      <button
        onClick={() => onRollback(activityId)}
        className="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700 transition-colors"
      >
        Rollback
      </button>
    </div>
  )
}

const ActivityCard = ({ activity, onExpand, onRollback, onPostMortem, isExpanded }) => {
  const icon = ACTIVITY_ICONS[activity.type] || '📋'
  const colorClass = ACTIVITY_COLORS[activity.type] || 'bg-gray-50 border-gray-200 text-gray-800'

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  const getStatusBadge = () => {
    if (activity.status === 'completed') {
      return (
        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
          ✓ Completed
        </span>
      )
    } else if (activity.status === 'rolled_back') {
      return (
        <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs font-medium rounded-full">
          ↶ Rolled Back
        </span>
      )
    } else if (activity.status === 'failed') {
      return (
        <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded-full">
          ✗ Failed
        </span>
      )
    }
    return null
  }

  return (
    <div className={`border-2 rounded-lg p-4 ${colorClass} transition-all hover:shadow-md`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start flex-1">
          <div className="text-3xl mr-3">{icon}</div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h4 className="font-semibold text-sm">{activity.title}</h4>
              {getStatusBadge()}
            </div>
            <p className="text-xs opacity-75 mb-2">{activity.description}</p>
            <div className="flex items-center text-xs opacity-60">
              <span>{formatTimestamp(activity.timestamp)}</span>
              {activity.approved_by && (
                <>
                  <span className="mx-2">•</span>
                  <span>by {activity.approved_by}</span>
                </>
              )}
            </div>

            {isExpanded && (
              <div className="mt-3 space-y-2">
                <div className="text-xs font-semibold opacity-80">Changes Made:</div>
                {activity.changes_made.map((change, idx) => (
                  <div key={idx} className="flex items-start text-xs p-2 bg-white/50 rounded">
                    <svg className="w-3 h-3 text-green-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <div className="font-medium">{change.action}</div>
                      <div className="opacity-70">{change.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activity.rollback.eligible && activity.rollback.expires_at && (
              <RollbackTimer
                expiresAt={activity.rollback.expires_at}
                activityId={activity.id}
                onRollback={onRollback}
              />
            )}

            {!activity.rollback.eligible && activity.rollback.reason && (
              <div className="mt-2 p-2 bg-gray-100 rounded text-xs opacity-70">
                {activity.rollback.reason}
              </div>
            )}

            {activity.status === 'rolled_back' && activity.rollback.performed_at && (
              <div className="mt-2 p-2 bg-orange-100 border border-orange-200 rounded text-xs">
                <div className="font-medium text-orange-800">Rolled back by {activity.rollback.performed_by}</div>
                <div className="text-orange-700">{new Date(activity.rollback.performed_at).toLocaleString()}</div>
              </div>
            )}

            {activity.status === 'completed' && (
              <button
                onClick={() => onPostMortem(activity.id)}
                className="mt-3 w-full px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Generate AI Post-Mortem
              </button>
            )}
          </div>
        </div>

        <button
          onClick={() => onExpand(activity.id)}
          className="ml-2 p-1 hover:bg-white/50 rounded transition-colors"
        >
          <svg
            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default function RecentActivities({ onToast }) {
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState(null)
  const [rollbackActivity, setRollbackActivity] = useState(null)
  const [postmortemActivity, setPostmortemActivity] = useState(null)

  useEffect(() => {
    fetchActivities()
  }, [])

  const fetchActivities = async () => {
    try {
      const response = await fetch('/api/activities?limit=6')
      const data = await response.json()
      setActivities(data.activities)
    } catch (error) {
      console.error('Error fetching activities:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRollback = (activityId) => {
    const activity = activities.find(a => a.id === activityId)
    if (activity) {
      setRollbackActivity(activity)
    }
  }

  const confirmRollback = async () => {
    if (!rollbackActivity) return

    try {
      onToast?.({
        type: 'info',
        title: 'Rollback Initiated',
        message: `Rolling back: ${rollbackActivity.title}`,
        duration: 3000
      })

      const response = await fetch(`/api/activities/${rollbackActivity.id}/rollback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ performed_by: 'demo-user' })
      })

      if (response.ok) {
        onToast?.({
          type: 'success',
          title: '✅ Rollback Successful',
          message: 'All changes have been reverted successfully',
          duration: 5000
        })
        setRollbackActivity(null)
        fetchActivities()
      } else {
        const error = await response.json()
        onToast?.({
          type: 'error',
          title: 'Rollback Failed',
          message: error.detail || 'Failed to rollback activity',
          duration: 5000
        })
        setRollbackActivity(null)
      }
    } catch (error) {
      console.error('Error performing rollback:', error)
      onToast?.({
        type: 'error',
        title: 'Rollback Error',
        message: 'An unexpected error occurred during rollback',
        duration: 5000
      })
      setRollbackActivity(null)
    }
  }

  const handleExpand = (activityId) => {
    setExpandedId(expandedId === activityId ? null : activityId)
  }

  const handlePostMortem = (activityId) => {
    const activity = activities.find(a => a.id === activityId)
    if (activity) {
      setPostmortemActivity(activity)
    }
  }

  if (loading) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">📋 Recent Activities</h3>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">📋 Recent Activities</h3>
          <span className="text-sm text-slate-400">{activities.length} activities</span>
        </div>

        {activities.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <p>No recent activities</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => (
              <ActivityCard
                key={activity.id}
                activity={activity}
                onExpand={handleExpand}
                onRollback={handleRollback}
                onPostMortem={handlePostMortem}
                isExpanded={expandedId === activity.id}
              />
            ))}
          </div>
        )}
      </div>

      {/* Rollback Modal */}
      {rollbackActivity && (
        <RollbackModal
          activity={rollbackActivity}
          onConfirm={confirmRollback}
          onCancel={() => setRollbackActivity(null)}
        />
      )}

      {/* Post-Mortem Modal */}
      {postmortemActivity && (
        <PostMortemModal
          activity={postmortemActivity}
          onClose={() => setPostmortemActivity(null)}
        />
      )}
    </>
  )
}
