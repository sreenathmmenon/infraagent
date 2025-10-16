import { useState } from 'react'

export default function RollbackModal({ activity, onConfirm, onCancel }) {
  const [isRollingBack, setIsRollingBack] = useState(false)
  const [rollbackStep, setRollbackStep] = useState(0)

  const handleConfirm = async () => {
    setIsRollingBack(true)

    // Simulate rollback steps
    const steps = activity.rollback.rollback_steps || []
    for (let i = 0; i < steps.length; i++) {
      setRollbackStep(i)
      await new Promise(resolve => setTimeout(resolve, 1500))
    }

    setRollbackStep(steps.length)
    await new Promise(resolve => setTimeout(resolve, 500))

    onConfirm()
  }

  if (!activity) return null

  const steps = activity.rollback.rollback_steps || []

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={!isRollingBack ? onCancel : undefined}></div>

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-xl shadow-2xl max-w-2xl w-full transform transition-all">
          {!isRollingBack ? (
            <>
              {/* Header */}
              <div className="bg-gradient-to-r from-orange-500 to-red-500 px-6 py-4 rounded-t-xl">
                <div className="flex items-center">
                  <svg className="w-8 h-8 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <h3 className="text-2xl font-bold text-white">Confirm Rollback</h3>
                </div>
              </div>

              {/* Content */}
              <div className="px-6 py-6">
                <div className="mb-6">
                  <div className="text-sm text-gray-600 mb-2">You are about to rollback:</div>
                  <div className="p-4 bg-orange-50 border-2 border-orange-200 rounded-lg">
                    <div className="font-semibold text-gray-900 text-lg">{activity.title}</div>
                    <div className="text-sm text-gray-600 mt-1">{activity.description}</div>
                  </div>
                </div>

                {/* Changes to revert */}
                <div className="mb-6">
                  <div className="text-sm font-semibold text-gray-700 mb-3">Changes that will be reverted:</div>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {activity.changes_made.map((change, idx) => (
                      <div key={idx} className="flex items-start p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <svg className="w-5 h-5 text-orange-500 mr-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                        </svg>
                        <div className="flex-1">
                          <div className="font-medium text-gray-900 text-sm">{change.action}</div>
                          <div className="text-xs text-gray-600">{change.detail}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Rollback steps */}
                {steps.length > 0 && (
                  <div className="mb-6">
                    <div className="text-sm font-semibold text-gray-700 mb-3">Rollback Steps:</div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <ol className="space-y-2 text-sm text-gray-700">
                        {steps.map((step, idx) => (
                          <li key={idx} className="flex items-start">
                            <span className="font-semibold mr-2">{idx + 1}.</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  </div>
                )}

                {/* Risk warning */}
                <div className="p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                  <div className="flex">
                    <svg className="w-5 h-5 text-yellow-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <div className="text-sm font-medium text-yellow-800">Warning</div>
                      <div className="text-sm text-yellow-700 mt-1">
                        This will revert all changes made by this activity. This action cannot be undone.
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="bg-gray-50 px-6 py-4 rounded-b-xl flex items-center justify-between">
                <button
                  onClick={onCancel}
                  className="px-6 py-2.5 bg-white border-2 border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirm}
                  className="px-6 py-2.5 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg font-medium hover:from-orange-600 hover:to-red-600 transition-colors shadow-lg"
                >
                  Confirm Rollback
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Rollback in Progress */}
              <div className="p-8">
                <div className="text-center mb-6">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-orange-100 rounded-full mb-4">
                    <svg className="w-10 h-10 text-orange-600 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Rolling Back Changes...</h3>
                  <p className="text-gray-600">Please wait while we revert the changes</p>
                </div>

                {/* Progress Steps */}
                <div className="space-y-3">
                  {steps.map((step, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center p-4 rounded-lg border-2 transition-all ${
                        idx < rollbackStep
                          ? 'bg-green-50 border-green-500'
                          : idx === rollbackStep
                          ? 'bg-blue-50 border-blue-500 animate-pulse'
                          : 'bg-gray-50 border-gray-300 opacity-50'
                      }`}
                    >
                      {idx < rollbackStep ? (
                        <svg className="w-6 h-6 text-green-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : idx === rollbackStep ? (
                        <svg className="w-6 h-6 text-blue-600 mr-3 flex-shrink-0 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <div className="w-6 h-6 mr-3 flex-shrink-0 rounded-full border-2 border-gray-400"></div>
                      )}
                      <span className={`text-sm font-medium ${
                        idx <= rollbackStep ? 'text-gray-900' : 'text-gray-500'
                      }`}>
                        {step}
                      </span>
                    </div>
                  ))}
                </div>

                {rollbackStep >= steps.length && (
                  <div className="mt-6 p-4 bg-green-100 border-2 border-green-500 rounded-lg text-center">
                    <svg className="w-12 h-12 text-green-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                    <div className="text-lg font-bold text-green-900">Rollback Complete!</div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
