import { useState } from 'react'

export default function AIAnalyzerPage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [nlAnswer, setNlAnswer] = useState(null)
  const [activeTab, setActiveTab] = useState('chat')  // 'chat', 'analyze', 'patterns'

  // Natural language query
  const handleNLQuery = async () => {
    if (!query.trim()) return

    setLoading(true)
    setNlAnswer(null)

    try {
      const response = await fetch('/api/ai/nl-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim(), hours: 24 })
      })

      if (response.ok) {
        const data = await response.json()
        setNlAnswer(data)
      }
    } catch (error) {
      console.error('Error:', error)
      setNlAnswer({ answer: 'Error: Could not connect to AI service' })
    } finally {
      setLoading(false)
    }
  }

  // Full AI analysis
  const handleFullAnalysis = async () => {
    setLoading(true)
    setAnalysis(null)

    try {
      // Look back 24 hours to catch test data
      const endTime = Date.now() / 1000
      const startTime = endTime - (24 * 3600)

      const response = await fetch('/api/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          include_remediation: true,
          start_time: startTime,
          end_time: endTime
        })
      })

      if (response.ok) {
        const data = await response.json()
        setAnalysis(data)
      }
    } catch (error) {
      console.error('Error:', error)
      setAnalysis({ status: 'error', message: 'Could not connect to AI service' })
    } finally {
      setLoading(false)
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const exampleQueries = [
    "Why are VMs failing to boot?",
    "What caused the authentication errors?",
    "Show me database connection issues",
    "Are there any anomalous patterns?",
    "What's causing the high error rate?"
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">🤖 AI Log Analyzer</h1>
        <p className="text-slate-400">Ask questions, get instant root cause analysis</p>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex gap-2 border-b border-slate-700">
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'chat'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            💬 AI Chat
          </button>
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'analyze'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            🔍 Full Analysis
          </button>
        </div>
      </div>

      {/* AI Chat Tab */}
      {activeTab === 'chat' && (
        <div className="max-w-7xl mx-auto">
          {/* Chat Input */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6 mb-6">
            <div className="flex gap-4 mb-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleNLQuery()}
                placeholder="Ask anything about your logs..."
                className="flex-1 bg-slate-700 text-white px-4 py-3 rounded-lg border border-slate-600 focus:outline-none focus:border-blue-500 text-lg"
              />
              <button
                onClick={handleNLQuery}
                disabled={loading || !query.trim()}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition-colors"
              >
                {loading ? '🤔 Thinking...' : '🚀 Ask AI'}
              </button>
            </div>

            {/* Example Queries */}
            <div className="flex flex-wrap gap-2">
              <span className="text-slate-400 text-sm">Examples:</span>
              {exampleQueries.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(ex)}
                  className="text-xs px-3 py-1 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded-full transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>

          {/* Answer */}
          {nlAnswer && (
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <div className="flex items-start gap-4">
                <div className="text-4xl">🤖</div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white mb-3">AI Answer</h3>
                  <div className="prose prose-invert max-w-none">
                    <p className="text-slate-200 text-lg leading-relaxed whitespace-pre-wrap">
                      {nlAnswer.answer}
                    </p>
                  </div>

                  {nlAnswer.confidence && (
                    <div className="mt-4 flex items-center gap-2">
                      <span className="text-slate-400 text-sm">Confidence:</span>
                      <div className="flex-1 bg-slate-700 rounded-full h-2 max-w-xs">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${nlAnswer.confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-slate-300 text-sm font-medium">
                        {(nlAnswer.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}

                  {nlAnswer.note && (
                    <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                      <p className="text-yellow-300 text-sm">ℹ️ {nlAnswer.note}</p>
                    </div>
                  )}

                  <div className="mt-4 text-xs text-slate-500">
                    Analyzed {nlAnswer.logs_analyzed} logs from last {nlAnswer.time_range_hours} hour(s)
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Full Analysis Tab */}
      {activeTab === 'analyze' && (
        <div className="max-w-7xl mx-auto">
          {/* Analyze Button */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              🔬 Deep Incident Analysis
            </h3>
            <p className="text-slate-400 mb-4">
              AI will analyze all logs from the last hour, detect patterns, correlate incidents,
              and provide root cause analysis with remediation suggestions.
            </p>
            <button
              onClick={handleFullAnalysis}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-slate-600 disabled:to-slate-600 text-white rounded-lg font-medium transition-colors"
            >
              {loading ? '🔄 Analyzing...' : '🚀 Run Full AI Analysis'}
            </button>
          </div>

          {/* Analysis Results */}
          {analysis && analysis.status === 'success' && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                  <div className="text-slate-400 text-sm mb-1">Logs Analyzed</div>
                  <div className="text-2xl font-bold text-white">{analysis.logs_analyzed}</div>
                </div>
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                  <div className="text-blue-400 text-sm mb-1">Unique Patterns</div>
                  <div className="text-2xl font-bold text-blue-300">
                    {analysis.patterns?.unique_patterns || 0}
                  </div>
                </div>
                <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                  <div className="text-purple-400 text-sm mb-1">Incidents Found</div>
                  <div className="text-2xl font-bold text-purple-300">
                    {analysis.incidents?.length || 0}
                  </div>
                </div>
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                  <div className="text-red-400 text-sm mb-1">Anomalies</div>
                  <div className="text-2xl font-bold text-red-300">
                    {analysis.anomalies?.length || 0}
                  </div>
                </div>
              </div>

              {/* Root Cause Analysis */}
              {analysis.root_cause_analysis && (
                <div className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    🎯 Root Cause Analysis
                  </h3>

                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-semibold text-red-300 mb-2">ROOT CAUSE</h4>
                      <p className="text-white text-lg">{analysis.root_cause_analysis.root_cause}</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-orange-300 mb-2">EXPLANATION</h4>
                      <p className="text-slate-200">{analysis.root_cause_analysis.explanation}</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-yellow-300 mb-2">IMPACT</h4>
                      <p className="text-slate-200">{analysis.root_cause_analysis.impact}</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-blue-300 mb-2">TIMELINE</h4>
                      <p className="text-slate-200">{analysis.root_cause_analysis.timeline_narrative}</p>
                    </div>

                    {/* Remediation */}
                    {analysis.root_cause_analysis.remediation && (
                      <div className="mt-6 pt-6 border-t border-slate-700">
                        <h4 className="text-lg font-semibold text-green-300 mb-4">💊 Remediation</h4>

                        <div className="space-y-4">
                          {analysis.root_cause_analysis.remediation.immediate_actions?.length > 0 && (
                            <div>
                              <h5 className="text-sm font-semibold text-green-400 mb-2">Immediate Actions</h5>
                              <ul className="list-disc list-inside space-y-1 text-slate-200">
                                {analysis.root_cause_analysis.remediation.immediate_actions.map((action, i) => (
                                  <li key={i}>{typeof action === 'string' ? action : action.action}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {analysis.root_cause_analysis.remediation.long_term_fixes?.length > 0 && (
                            <div>
                              <h5 className="text-sm font-semibold text-blue-400 mb-2">Long-term Fixes</h5>
                              <ul className="list-disc list-inside space-y-1 text-slate-200">
                                {analysis.root_cause_analysis.remediation.long_term_fixes.map((fix, i) => (
                                  <li key={i}>{typeof fix === 'string' ? fix : fix.action}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {analysis.root_cause_analysis.remediation.prevention?.length > 0 && (
                            <div>
                              <h5 className="text-sm font-semibold text-purple-400 mb-2">Prevention</h5>
                              <ul className="list-disc list-inside space-y-1 text-slate-200">
                                {analysis.root_cause_analysis.remediation.prevention.map((item, i) => (
                                  <li key={i}>{item}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {analysis.root_cause_analysis.note && (
                      <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                        <p className="text-yellow-300 text-sm">ℹ️ {analysis.root_cause_analysis.note}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Incidents */}
              {analysis.incidents && analysis.incidents.length > 0 && (
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4">
                    🔗 Correlated Incidents
                  </h3>

                  <div className="space-y-4">
                    {analysis.incidents.slice(0, 3).map((incident, i) => (
                      <div key={i} className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold text-white">
                            Incident #{incident.incident_id}
                          </h4>
                          <span className={`px-2 py-1 rounded text-xs font-bold ${
                            incident.severity === 'CRITICAL' ? 'bg-red-500' :
                            incident.severity === 'ERROR' ? 'bg-orange-500' :
                            'bg-yellow-500'
                          } text-white`}>
                            {incident.severity}
                          </span>
                        </div>

                        <p className="text-slate-300 text-sm mb-3">{incident.narrative}</p>

                        <div className="flex flex-wrap gap-2 mb-3">
                          {incident.affected_services?.map((service, j) => (
                            <span key={j} className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs">
                              {service}
                            </span>
                          ))}
                        </div>

                        <div className="text-xs text-slate-500">
                          {incident.log_count} logs • {incident.duration_seconds?.toFixed(0)}s duration •
                          {' '}{formatTimestamp(incident.start_time)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Patterns */}
              {analysis.patterns?.patterns?.length > 0 && (
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                  <h3 className="text-xl font-bold text-white mb-4">
                    📊 Detected Patterns
                  </h3>

                  <div className="space-y-3">
                    {analysis.patterns.patterns.slice(0, 5).map((pattern, i) => (
                      <div key={i} className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                              pattern.severity === 'ERROR' ? 'bg-red-500' :
                              pattern.severity === 'WARN' ? 'bg-yellow-500' :
                              'bg-blue-500'
                            } text-white`}>
                              {pattern.severity}
                            </span>
                            <span className="text-sm font-mono bg-black/20 px-2 py-1 rounded text-slate-300">
                              {pattern.count}x
                            </span>
                            {pattern.is_critical && (
                              <span className="text-xs px-2 py-1 bg-red-500/20 text-red-300 rounded">
                                🔥 CRITICAL
                              </span>
                            )}
                          </div>
                        </div>

                        <p className="text-slate-200 text-sm font-mono">{pattern.template}</p>

                        <div className="mt-2 flex flex-wrap gap-2">
                          {pattern.services?.map((service, j) => (
                            <span key={j} className="text-xs px-2 py-1 bg-slate-600 text-slate-300 rounded">
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {analysis && analysis.status === 'no_data' && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-12 text-center">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-slate-300 text-lg">No logs found for analysis</p>
              <p className="text-slate-500 text-sm mt-2">Generate some test data first</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
