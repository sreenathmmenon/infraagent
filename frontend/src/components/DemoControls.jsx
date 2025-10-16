import { useState } from 'react'

export default function DemoControls() {
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const scenarios = [
    {
      id: 1,
      name: 'CPU Spike',
      description: 'High CPU requiring config scale',
      severity: 'HIGH',
      icon: '🔥',
      confidence: 87
    },
    {
      id: 2,
      name: 'Disk Full',
      description: 'Critical disk space issue',
      severity: 'CRITICAL',
      icon: '💾',
      confidence: 92
    },
    {
      id: 3,
      name: 'High Latency',
      description: 'Network path optimization needed',
      severity: 'MEDIUM',
      icon: '🌐',
      confidence: 78
    }
  ]

  const triggerScenario = async (scenarioId) => {
    setLoading(true)
    try {
      const response = await fetch('/api/alerts/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ scenario: scenarioId })
      })

      if (response.ok) {
        console.log(`Triggered scenario ${scenarioId}`)
        setIsOpen(false)
      }
    } catch (error) {
      console.error('Error triggering scenario:', error)
      alert('Failed to trigger scenario')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Demo Controls Panel */}
      <div className={`fixed bottom-6 right-6 transition-all duration-300 ${
        isOpen ? 'w-80' : 'w-auto'
      }`}>
        {!isOpen ? (
          <button
            onClick={() => setIsOpen(true)}
            className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-full px-6 py-4 shadow-lg
                     hover:from-blue-700 hover:to-blue-800 hover:shadow-xl
                     transform hover:scale-105
                     transition-all duration-200
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                     flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="font-semibold">Simulate Alert</span>
          </button>
        ) : (
          <div className="bg-white rounded-xl shadow-2xl overflow-hidden border border-gray-200">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-4 py-3 flex items-center justify-between">
              <h3 className="text-white font-semibold flex items-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Demo Scenarios
              </h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-white hover:bg-white/20 rounded p-1 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Scenarios */}
            <div className="p-4 space-y-3">
              {scenarios.map((scenario) => (
                <button
                  key={scenario.id}
                  onClick={() => triggerScenario(scenario.id)}
                  disabled={loading}
                  className="w-full text-left p-4 rounded-lg border-2 border-gray-200
                           hover:border-blue-300 hover:bg-blue-50
                           transition-all duration-200
                           disabled:opacity-50 disabled:cursor-not-allowed
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <div className="flex items-start">
                    <span className="text-2xl mr-3">{scenario.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-semibold text-gray-900">{scenario.name}</h4>
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          scenario.severity === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                          scenario.severity === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                          'bg-yellow-100 text-yellow-700'
                        }`}>
                          {scenario.severity}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{scenario.description}</p>
                      <div className="flex items-center text-xs text-gray-500">
                        <svg className="w-4 h-4 mr-1 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {scenario.confidence}% confidence
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
              <p className="text-xs text-gray-600 text-center">
                Click a scenario to simulate an infrastructure alert
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
