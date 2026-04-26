import { useState } from 'react'

export default function EmailCard({ email, onDecide }) {
  const [deciding, setDeciding] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const decide = async (decision) => {
    if (deciding) return
    setDeciding(true)
    try {
      await onDecide(email.id, decision)
    } finally {
      setDeciding(false)
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs px-2 py-0.5 rounded bg-indigo-900 text-indigo-300 font-medium">
              {email.email_type ?? 'hr'}
            </span>
          </div>
          <h3 className="text-base font-semibold text-white">{email.company_name}</h3>
          <p className="text-sm text-gray-400 mt-0.5">
            {email.hr_email} · {email.company_domain}
          </p>
        </div>
      </div>

      {email.subject && (
        <p className="mt-3 text-sm text-gray-300">
          <span className="text-gray-500">Subject:</span> {email.subject}
        </p>
      )}

      {email.body && (
        <>
          <button
            onClick={() => setExpanded(e => !e)}
            className="mt-2 text-xs text-indigo-400 hover:text-indigo-300"
          >
            {expanded ? 'Hide email body' : 'Preview email body'}
          </button>
          {expanded && (
            <pre className="mt-2 text-sm text-gray-400 whitespace-pre-wrap leading-relaxed">
              {email.body}
            </pre>
          )}
        </>
      )}

      <div className="flex gap-3 mt-4">
        <button
          onClick={() => decide('yes')}
          disabled={deciding}
          className="flex-1 py-2.5 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 font-semibold text-white transition-colors"
        >
          SEND ✓
        </button>
        <button
          onClick={() => decide('no')}
          disabled={deciding}
          className="w-24 py-2.5 rounded-lg bg-gray-800 hover:bg-red-900 hover:text-red-300 disabled:opacity-50 font-medium text-gray-400 transition-colors"
        >
          SKIP ✕
        </button>
      </div>
    </div>
  )
}
