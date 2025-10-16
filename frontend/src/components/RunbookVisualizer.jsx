import { useState, useEffect } from 'react'

const RunbookStep = ({ step, isActive, isCompleted }) => {
  return (
    <div className={`flex items-start p-3 rounded-lg border-2 transition-all ${
      isActive
        ? 'bg-blue-50 border-blue-500 animate-pulse'
        : isCompleted
        ? 'bg-green-50 border-green-500'
        : 'bg-gray-50 border-gray-300 opacity-50'
    }`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold mr-3 ${
        isActive
          ? 'bg-blue-500 text-white'
          : isCompleted
          ? 'bg-green-500 text-white'
          : 'bg-gray-300 text-gray-600'
      }`}>
        {isCompleted ? (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          step.step
        )}
      </div>

      <div className="flex-1">
        <div className={`font-semibold mb-1 ${
          isActive ? 'text-blue-900' : isCompleted ? 'text-green-900' : 'text-gray-700'
        }`}>
          {step.name}
        </div>
        <div className={`text-sm mb-1 ${
          isActive ? 'text-blue-700' : isCompleted ? 'text-green-700' : 'text-gray-600'
        }`}>
          {step.description}
        </div>
        <div className={`text-xs ${
          isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-500'
        }`}>
          ⏱️ {step.estimated_time}
        </div>

        {isActive && (
          <div className="mt-2 flex items-center">
            <svg className="animate-spin h-4 w-4 text-blue-600 mr-2" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm text-blue-700 font-medium">Executing...</span>
          </div>
        )}

        {step.rollback_impact && (
          <div className="mt-2 text-xs p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800">
            <span className="font-semibold">Rollback Impact:</span> {step.rollback_impact}
          </div>
        )}
      </div>
    </div>
  )
}

export default function RunbookVisualizer({ runbookId, currentStep = 0 }) {
  const [runbook, setRunbook] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (runbookId) {
      fetchRunbook()
    }
  }, [runbookId])

  const fetchRunbook = async () => {
    try {
      const response = await fetch(`/api/runbooks/${runbookId}`)
      if (response.ok) {
        const data = await response.json()
        setRunbook(data)
      }
    } catch (error) {
      console.error('Error fetching runbook:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !runbook) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-blue-200">
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  const completedSteps = currentStep
  const progress = ((completedSteps) / runbook.steps.length) * 100

  return (
    <div className="bg-white rounded-xl shadow-2xl border-2 border-blue-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-indigo-600 p-6 rounded-t-xl">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-blue-100 text-sm font-medium mb-1">Automated Runbook</div>
            <h3 className="text-2xl font-bold text-white mb-2">{runbook.title}</h3>
            <p className="text-blue-100 text-sm">{runbook.description}</p>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2 text-center">
            <div className="text-white text-xs mb-1">Success Rate</div>
            <div className="text-white text-2xl font-bold">{runbook.success_rate}%</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-white text-sm mb-2">
            <span>Progress</span>
            <span>{Math.round(progress)}% • Step {completedSteps}/{runbook.steps.length}</span>
          </div>
          <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-green-400 to-emerald-500 h-full transition-all duration-500 rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Steps */}
      <div className="p-6">
        <div className="space-y-3">
          {runbook.steps.map((step, index) => (
            <RunbookStep
              key={step.step}
              step={step}
              isActive={index === currentStep}
              isCompleted={index < currentStep}
            />
          ))}
        </div>

        {/* Risk Assessment */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-sm font-semibold text-gray-700 mb-2">📊 Risk Assessment</div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Risk Level:</span>
              <span className={`ml-2 font-semibold ${
                runbook.risk_assessment.risk_level === 'low'
                  ? 'text-green-600'
                  : runbook.risk_assessment.risk_level === 'medium'
                  ? 'text-yellow-600'
                  : 'text-red-600'
              }`}>
                {runbook.risk_assessment.risk_level.toUpperCase()}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Duration:</span>
              <span className="ml-2 font-semibold text-gray-800">{runbook.estimated_duration}</span>
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-600">
            <div className="font-medium mb-1">Impact:</div>
            <div>{runbook.risk_assessment.potential_impact}</div>
            <div className="mt-1 font-medium">Mitigation:</div>
            <div>{runbook.risk_assessment.mitigation}</div>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <div>
            <span className="font-medium">Executed:</span>
            <span className="ml-2">{runbook.execution_count} times</span>
          </div>
          {runbook.last_used && (
            <div>
              <span className="font-medium">Last used:</span>
              <span className="ml-2">{new Date(runbook.last_used).toLocaleDateString()}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
