import { useState, useEffect, useCallback } from 'react'
import { api } from './api/client'
import Sidebar from './components/Sidebar'
import StatsBar from './components/StatsBar'
import JobCard from './components/JobCard'
import EmailCard from './components/EmailCard'

export default function App() {
  const [view, setView] = useState('pending')
  const [pendingJobs, setPendingJobs] = useState([])
  const [pendingEmails, setPendingEmails] = useState([])
  const [appliedJobs, setAppliedJobs] = useState([])
  const [failedJobs, setFailedJobs] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [jobs, emails, statsData, history, failed] = await Promise.all([
        api.getPendingJobs(),
        api.getPendingEmails(),
        api.getStats(),
        api.getHistory(),
        api.getFailed(),
      ])
      setPendingJobs(jobs)
      setPendingEmails(emails)
      setStats(statsData)
      setAppliedJobs(history)
      setFailedJobs(failed)
      setLastRefresh(new Date())
    } catch (e) {
      console.error('Refresh failed:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 10000)
    return () => clearInterval(interval)
  }, [refresh])

  const handleJobDecision = async (jobId, decision) => {
    await api.decideJob(jobId, decision)
    setPendingJobs(prev => prev.filter(j => j.id !== jobId))
    refresh()
  }

  const handleEmailDecision = async (emailId, decision) => {
    await api.decideEmail(emailId, decision)
    setPendingEmails(prev => prev.filter(e => e.id !== emailId))
    refresh()
  }

  const counts = {
    pending: pendingJobs.length,
    emails: pendingEmails.length,
    applied: appliedJobs.length,
    failed: failedJobs.length,
  }

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      <Sidebar view={view} setView={setView} counts={counts} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <StatsBar stats={stats} lastRefresh={lastRefresh} />

        <main className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-400 text-lg">Loading...</div>
            </div>
          ) : view === 'pending' ? (
            <JobsView
              jobs={pendingJobs}
              onDecide={handleJobDecision}
              emptyMsg="No pending jobs — system is hunting..."
            />
          ) : view === 'emails' ? (
            <EmailsView
              emails={pendingEmails}
              onDecide={handleEmailDecision}
              emptyMsg="No pending cold emails"
            />
          ) : view === 'applied' ? (
            <JobsView
              jobs={appliedJobs}
              readOnly
              emptyMsg="No applied jobs yet"
            />
          ) : view === 'failed' ? (
            <JobsView
              jobs={failedJobs}
              readOnly
              emptyMsg="No failed jobs"
            />
          ) : null}
        </main>
      </div>
    </div>
  )
}

function JobsView({ jobs, onDecide, readOnly, emptyMsg }) {
  if (!jobs.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500 text-lg">{emptyMsg}</p>
      </div>
    )
  }
  return (
    <div className="grid gap-4 max-w-3xl mx-auto">
      {jobs.map(job => (
        <JobCard key={job.id} job={job} onDecide={onDecide} readOnly={readOnly} />
      ))}
    </div>
  )
}

function EmailsView({ emails, onDecide, emptyMsg }) {
  if (!emails.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500 text-lg">{emptyMsg}</p>
      </div>
    )
  }
  return (
    <div className="grid gap-4 max-w-3xl mx-auto">
      {emails.map(email => (
        <EmailCard key={email.id} email={email} onDecide={onDecide} />
      ))}
    </div>
  )
}
