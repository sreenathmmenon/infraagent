import { useState } from 'react'

export default function ApprovalDashboard({ workflow, onApprove, onReject }) {
  const [isApproving, setIsApproving] = useState(false)

  const handleApprove = async () => {
    setIsApproving(true)
    await onApprove()
  }

  if (!workflow) return null

  const {
    alert,
    analysis,
    topology,
    suggestion,
    agent_steps,
    historical_context,
    time_savings,
    confidence_breakdown,
    mcp_info
  } = workflow

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-xl shadow-2xl overflow-hidden">
        {/* Alert Header */}
        <div className="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-500 p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
            <div className="ml-4 flex-1">
              <h2 className="text-2xl font-bold text-gray-900">
                {alert.type.replace(/_/g, ' ')}
              </h2>
              <p className="text-gray-600 mt-1">
                Detected on <span className="font-semibold">{alert.source}</span> at {new Date(alert.timestamp).toLocaleTimeString()}
              </p>
              <div className="flex items-center gap-4 mt-3">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  alert.severity === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                  alert.severity === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>
                  {alert.severity}
                </span>
                <span className="text-sm text-gray-600">
                  {alert.description}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Time Savings Banner */}
        {time_savings && (
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-500 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-green-900 mb-1">⚡ Time & Cost Savings</h3>
                <p className="text-green-700">
                  <span className="text-3xl font-bold">{time_savings.time_saved_formatted}</span>
                  <span className="text-sm ml-2">saved vs manual resolution</span>
                </p>
              </div>
              <div className="text-right">
                <div className="text-sm text-green-700 mb-1">AI: {time_savings.ai_time_formatted}</div>
                <div className="text-sm text-gray-500 line-through">Manual: {time_savings.manual_time_formatted}</div>
                <div className="text-lg font-bold text-green-600 mt-2">${time_savings.cost_saved} saved</div>
              </div>
            </div>
          </div>
        )}

        {/* Historical Context Banner */}
        {historical_context && historical_context.found && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500 p-6">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
              </div>
              <div className="ml-4 flex-1">
                <h3 className="text-lg font-bold text-blue-900 mb-2">🧠 AI Learned from History</h3>
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{historical_context.count}</div>
                    <div className="text-xs text-blue-700">Similar Incidents</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">{historical_context.success_rate}%</div>
                    <div className="text-xs text-blue-700">Success Rate</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">{historical_context.avg_resolution_time_formatted}</div>
                    <div className="text-xs text-blue-700">Avg Resolution</div>
                  </div>
                </div>
                {historical_context.learning_insights && historical_context.learning_insights.length > 0 && (
                  <div className="space-y-1">
                    {historical_context.learning_insights.map((insight, i) => (
                      <div key={i} className="text-sm text-blue-800">• {insight}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MCP Integration Badge */}
        {mcp_info && mcp_info.enabled && (
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-l-4 border-purple-500 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <div className="text-sm font-bold text-purple-900">Model Context Protocol (MCP) Enabled</div>
                  <div className="text-xs text-purple-700">Compatible with HPE GreenLake Intelligence & OpenAI ChatGPT</div>
                </div>
              </div>
              <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full">
                {mcp_info.capabilities.tools} Tools Available
              </span>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="p-8 space-y-8">
          {/* Agent Timeline */}
          <Section title="AI Analysis Pipeline">
            <div className="relative">
              {agent_steps.map((step, index) => (
                <div key={index} className="flex items-start mb-6 last:mb-0">
                  <div className="flex flex-col items-center mr-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      step.completed ? 'bg-green-500' : 'bg-gray-300'
                    }`}>
                      {step.completed ? (
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <span className="text-white font-semibold">{index + 1}</span>
                      )}
                    </div>
                    {index < agent_steps.length - 1 && (
                      <div className="w-0.5 h-16 bg-gray-300 my-1"></div>
                    )}
                  </div>
                  <div className="flex-1 pt-1">
                    <h4 className="font-semibold text-gray-900">{step.agent_name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                    <span className="text-xs text-gray-400 mt-1 inline-block">{step.duration}</span>
                  </div>
                </div>
              ))}
            </div>
          </Section>

          {/* Impact Assessment */}
          <Section title="Impact Assessment">
            <div className="grid grid-cols-3 gap-6">
              <MetricCard
                label="Severity"
                value={alert.severity}
                color={alert.severity === 'CRITICAL' ? 'red' : alert.severity === 'HIGH' ? 'orange' : 'yellow'}
                icon={(
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                )}
              />
              <MetricCard
                label="Affected Services"
                value={topology.affected_count}
                color="blue"
                icon={(
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                )}
              />
              <MetricCard
                label="AI Confidence"
                value={`${suggestion.confidence}%`}
                color="green"
                icon={(
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              />
            </div>
          </Section>

          {/* Confidence Breakdown */}
          {confidence_breakdown && (
            <Section title="AI Confidence Breakdown">
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <div className="text-4xl font-bold text-indigo-600">{confidence_breakdown.total_confidence}%</div>
                    <div className="text-sm text-indigo-700 mt-1">Overall Confidence - {confidence_breakdown.confidence_level}</div>
                  </div>
                  <div className="w-20 h-20 relative">
                    <svg className="w-20 h-20 transform -rotate-90">
                      <circle cx="40" cy="40" r="36" stroke="#e0e7ff" strokeWidth="8" fill="none" />
                      <circle
                        cx="40"
                        cy="40"
                        r="36"
                        stroke="#4f46e5"
                        strokeWidth="8"
                        fill="none"
                        strokeDasharray={`${confidence_breakdown.total_confidence * 2.26} 226`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center text-indigo-600 font-bold">
                      {confidence_breakdown.total_confidence}%
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  {confidence_breakdown.components && confidence_breakdown.components.map((component, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-gray-700">{component.factor}</span>
                        <span className="text-sm font-bold text-indigo-600">{component.contribution}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-purple-500 h-3 rounded-full transition-all duration-1000"
                          style={{ width: `${component.contribution}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">{component.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            </Section>
          )}

          {/* Root Cause Analysis */}
          <Section title="Root Cause Analysis">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <p className="text-blue-900 font-medium mb-4">
                {analysis.root_cause}
              </p>
              <div className="space-y-2">
                <div className="text-sm font-semibold text-blue-800 mb-2">Confidence Reasoning:</div>
                {suggestion.confidence_reasoning.map((reason, index) => (
                  <div key={index} className="flex items-start text-sm text-blue-800">
                    <svg className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
            </div>
          </Section>

          {/* Recommended Fix */}
          <Section title="Recommended Fix">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="font-bold text-blue-900 text-lg mb-2">
                    {suggestion.recommended_action.title}
                  </h4>
                  <p className="text-blue-800">
                    {suggestion.recommended_action.description}
                  </p>
                </div>
                <div className="ml-4">
                  <div className="text-right">
                    <div className="text-3xl font-bold text-blue-600">{suggestion.confidence}%</div>
                    <div className="text-xs text-blue-700 uppercase tracking-wide">Confidence</div>
                  </div>
                </div>
              </div>

              {/* Config Changes Preview */}
              {suggestion.config_before && suggestion.config_after && (
                <div className="mt-6">
                  <div className="text-sm font-semibold text-blue-900 mb-3">Configuration Changes:</div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="bg-red-100 text-red-800 px-3 py-1.5 text-xs font-semibold rounded-t">Before</div>
                      <pre className="bg-red-50 p-4 text-xs overflow-x-auto rounded-b border border-red-200 text-gray-800">
                        {suggestion.config_before}
                      </pre>
                    </div>
                    <div>
                      <div className="bg-green-100 text-green-800 px-3 py-1.5 text-xs font-semibold rounded-t">After</div>
                      <pre className="bg-green-50 p-4 text-xs overflow-x-auto rounded-b border border-green-200 text-gray-800">
                        {suggestion.config_after}
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {/* Expected Outcome */}
              <div className="mt-6 bg-white/80 rounded-lg p-4 border border-blue-200">
                <div className="text-sm font-semibold text-blue-900 mb-2">Expected Outcome:</div>
                <div className="flex items-center justify-between text-sm">
                  <div>
                    <span className="text-gray-600">{suggestion.expected_outcome.metric}: </span>
                    <span className="text-red-600 font-semibold line-through">{suggestion.expected_outcome.current}</span>
                    <span className="mx-2">→</span>
                    <span className="text-green-600 font-semibold">{suggestion.expected_outcome.expected}</span>
                  </div>
                  <div className="text-gray-500">
                    Timeline: {suggestion.expected_outcome.timeline}
                  </div>
                </div>
              </div>
            </div>
          </Section>

          {/* Rollback Plan */}
          <Section title="Rollback Plan">
            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <div className="flex items-start mb-4">
                <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  suggestion.risk_assessment.level === 'VERY_LOW' || suggestion.risk_assessment.level === 'LOW'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  Risk: {suggestion.risk_assessment.level.replace(/_/g, ' ')}
                </div>
              </div>
              <ol className="list-decimal list-inside space-y-2 text-gray-700">
                {suggestion.rollback_plan.map((step, index) => (
                  <li key={index} className="text-sm">{step}</li>
                ))}
              </ol>
            </div>
          </Section>

          {/* Alternative Options (collapsed by default) */}
          {suggestion.alternatives && suggestion.alternatives.length > 0 && (
            <Section title="Alternative Options">
              <div className="space-y-3">
                {suggestion.alternatives.map((alt, index) => (
                  <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h5 className="font-semibold text-gray-900">{alt.title}</h5>
                        <p className="text-sm text-gray-600 mt-1">{alt.description}</p>
                        {alt.caveat && (
                          <p className="text-sm text-orange-600 mt-2">⚠️ {alt.caveat}</p>
                        )}
                      </div>
                      <div className="ml-4 text-right">
                        <div className="text-sm font-semibold text-gray-700">{alt.confidence}%</div>
                        <div className="text-xs text-gray-500">{alt.effort} effort</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>

        {/* THE CRITICAL BUTTONS */}
        <div className="bg-gray-50 px-8 py-6 flex items-center justify-between border-t border-gray-200">
          <div className="text-sm text-gray-600">
            <svg className="w-5 h-5 inline mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Human approval required before AI can execute changes
          </div>
          <div className="flex space-x-4">
            <button
              onClick={onReject}
              disabled={isApproving}
              className="px-8 py-3 border-2 border-gray-300 rounded-lg font-semibold text-gray-700
                       hover:bg-gray-100 hover:border-gray-400
                       transition-all duration-200
                       focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2
                       disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Reject suggested fix"
            >
              Reject
            </button>

            <button
              onClick={handleApprove}
              disabled={isApproving}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg
                       font-semibold text-white shadow-lg
                       hover:from-blue-700 hover:to-blue-800 hover:shadow-xl
                       transform hover:scale-105
                       transition-all duration-200
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                       disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              aria-label="Approve and execute suggested fix"
            >
              {isApproving ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Approving...
                </span>
              ) : (
                <span className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Approve & Execute
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Supporting Components

function Section({ title, children }) {
  return (
    <div>
      <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
        {title}
      </h3>
      {children}
    </div>
  )
}

function MetricCard({ label, value, color, icon }) {
  const colorClasses = {
    red: 'bg-red-50 border-red-200 text-red-700',
    orange: 'bg-orange-50 border-orange-200 text-orange-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    green: 'bg-green-50 border-green-200 text-green-700'
  }

  return (
    <div className={`${colorClasses[color]} border-2 rounded-lg p-6 text-center`}>
      <div className="flex justify-center mb-3">
        {icon}
      </div>
      <div className="text-3xl font-bold mb-2">{value}</div>
      <div className="text-sm font-medium opacity-90">{label}</div>
    </div>
  )
}
