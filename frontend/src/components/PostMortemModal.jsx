import { useState, useEffect } from 'react'

export default function PostMortemModal({ activity, onClose }) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const generateReport = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/activities/${activity.id}/postmortem`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error('Failed to generate report')
      }

      const data = await response.json()
      setReport(data.report)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Auto-generate on mount
  useEffect(() => {
    generateReport()
  }, [])

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Incident Post-Mortem</h2>
            <p className="text-sm text-gray-600 mt-1">{activity.title}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Generating AI-powered post-mortem report...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">Error: {error}</p>
            </div>
          )}

          {report && (
            <div className="space-y-6">
              {/* Incident ID */}
              <div className="bg-gray-50 rounded-lg p-4">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Incident ID
                </span>
                <p className="text-lg font-mono font-bold text-gray-900 mt-1">
                  {report.incident_id}
                </p>
                {report.generated_by === 'AI' && (
                  <span className="inline-block mt-2 px-2 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded">
                    ✨ AI-Generated
                  </span>
                )}
              </div>

              {/* Executive Summary */}
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Executive Summary</h3>
                <p className="text-gray-700 leading-relaxed">{report.summary}</p>
              </section>

              {/* Timeline */}
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Timeline</h3>
                <div className="space-y-2">
                  {report.timeline.map((event, idx) => (
                    <div key={idx} className="flex gap-4 items-start">
                      <span className="font-mono text-sm text-gray-600 font-semibold min-w-[60px]">
                        {event.time}
                      </span>
                      <span className="text-gray-700">{event.event}</span>
                    </div>
                  ))}
                </div>
              </section>

              {/* Root Cause */}
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Root Cause Analysis</h3>
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-1 bg-orange-200 text-orange-800 text-xs font-semibold rounded">
                      {report.root_cause.category}
                    </span>
                  </div>
                  <p className="text-gray-700 mb-3">{report.root_cause.description}</p>
                  <div className="mt-3">
                    <span className="text-sm font-semibold text-gray-700">Contributing Factors:</span>
                    <ul className="mt-1 ml-4 list-disc text-sm text-gray-600 space-y-1">
                      {report.root_cause.contributing_factors.map((factor, idx) => (
                        <li key={idx}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>

              {/* Impact */}
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Impact</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <span className="text-xs font-semibold text-gray-600 uppercase">Duration</span>
                    <p className="text-lg font-bold text-gray-900 mt-1">{report.impact.duration}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <span className="text-xs font-semibold text-gray-600 uppercase">Requests Affected</span>
                    <p className="text-lg font-bold text-gray-900 mt-1">
                      {report.impact.estimated_requests_affected}
                    </p>
                  </div>
                </div>
                <div className="mt-3 text-sm text-gray-700">
                  <p><strong>Services:</strong> {report.impact.services_affected.join(', ')}</p>
                  <p className="mt-1"><strong>User Impact:</strong> {report.impact.user_impact}</p>
                </div>
              </section>

              {/* Resolution */}
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Resolution</h3>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-sm text-gray-700 mb-2">
                    <strong>Time to Resolve:</strong> {report.resolution.time_to_resolve}
                  </p>
                  <p className="text-sm font-semibold text-gray-700 mb-2">Actions Taken:</p>
                  <ul className="ml-4 list-disc text-sm text-gray-600 space-y-1">
                    {report.resolution.actions_taken.map((action, idx) => (
                      <li key={idx}>{action}</li>
                    ))}
                  </ul>
                  <p className="text-sm text-gray-700 mt-3">
                    <strong>Verification:</strong> {report.resolution.verification}
                  </p>
                </div>
              </section>

              {/* Lessons Learned */}
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Lessons Learned</h3>
                <div className="space-y-3">
                  {report.lessons_learned.map((lesson, idx) => (
                    <div key={idx} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      {lesson.what_went_well && (
                        <p className="text-sm">
                          <span className="font-semibold text-green-700">✓ What went well:</span>{' '}
                          <span className="text-gray-700">{lesson.what_went_well}</span>
                        </p>
                      )}
                      {lesson.what_could_improve && (
                        <p className="text-sm">
                          <span className="font-semibold text-orange-700">⚠ What could improve:</span>{' '}
                          <span className="text-gray-700">{lesson.what_could_improve}</span>
                        </p>
                      )}
                      {lesson.action_item && (
                        <p className="text-sm">
                          <span className="font-semibold text-blue-700">→ Action item:</span>{' '}
                          <span className="text-gray-700">{lesson.action_item}</span>
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </section>

              {/* Preventive Measures */}
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Preventive Measures</h3>
                <ul className="space-y-2">
                  {report.preventive_measures.map((measure, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span className="text-gray-700">{measure}</span>
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
