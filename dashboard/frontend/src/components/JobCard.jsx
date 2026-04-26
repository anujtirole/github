import { useState } from 'react'

const PLATFORM_COLORS = {
  linkedin: 'bg-blue-900 text-blue-300',
  naukri: 'bg-orange-900 text-orange-300',
  indeed: 'bg-purple-900 text-purple-300',
  internshala: 'bg-teal-900 text-teal-300',
}

export default function JobCard({ job, onDecide, readOnly }) {
  const [expanded, setExpanded] = useState(false)
  const [deciding, setDeciding] = useState(false)

  const score = job.relevance_score ?? 0
  const scoreColor = score >= 80 ? 'text-green-400' : score >= 60 ? 'text-yellow-400' : 'text-orange-400'

  const decide = async (decision) => {
    if (deciding || !onDecide) return
    setDeciding(true)
    try {
      await onDecide(job.id, decision)
    } finally {
      setDeciding(false)
    }
  }

  const statusColor = {
    APPLIED: 'text-green-400',
    FAILED: 'text-red-400',
    FAILED_PERMANENT: 'text-red-600',
    PENDING_APPROVAL: 'text-yellow-400',
    APPROVED: 'text-blue-400',
  }[job.status] ?? 'text-gray-400'

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${PLATFORM_COLORS[job.platform] ?? 'bg-gray-800 text-gray-400'}`}>
              {job.platform}
            </span>
            {readOnly && (
              <span className={`text-xs font-medium ${statusColor}`}>{job.status}</span>
            )}
          </div>
          <h3 className="text-base font-semibold text-white truncate">{job.title}</h3>
          <p className="text-sm text-gray-400 mt-0.5">
            {job.company}
            {job.location ? ` · ${job.location}` : ''}
          </p>
        </div>

        <div className="text-right shrink-0">
          <div className={`text-2xl font-bold ${scoreColor}`}>{score}</div>
          <div className="text-xs text-gray-500">/ 100</div>
        </div>
      </div>

      {score > 0 && (
        <div className="mt-3">
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-green-400"
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
      )}

      {job.error_log && !readOnly && (
        <p className="mt-2 text-xs text-gray-500 italic">“{job.error_log}”</p>
      )}

      {job.description && (
        <button
          onClick={() => setExpanded(e => !e)}
          className="mt-2 text-xs text-indigo-400 hover:text-indigo-300"
        >
          {expanded ? 'Hide description' : 'View description'}
        </button>
      )}

      {expanded && (
        <p className="mt-2 text-sm text-gray-400 leading-relaxed line-clamp-6">
          {job.description}
        </p>
      )}

      {job.job_url && (
        <a
          href={job.job_url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-xs text-indigo-400 hover:underline"
        >
          View job posting ↗
        </a>
      )}

      {!readOnly && (
        <div className="flex gap-3 mt-4">
          <button
            onClick={() => decide('yes')}
            disabled={deciding}
            className="flex-1 py-2.5 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 font-semibold text-white transition-colors"
          >
            YES ✓
          </button>
          <button
            onClick={() => decide('no')}
            disabled={deciding}
            className="w-24 py-2.5 rounded-lg bg-gray-800 hover:bg-red-900 hover:text-red-300 disabled:opacity-50 font-medium text-gray-400 transition-colors"
          >
            NO ✕
          </button>
        </div>
      )}
    </div>
  )
}
