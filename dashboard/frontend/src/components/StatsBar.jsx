export default function StatsBar({ stats, lastRefresh }) {
  const items = [
    { label: 'Applied Today', value: stats.applied_today ?? 0, color: 'text-green-400' },
    { label: 'Total Applied', value: stats.applied_total ?? 0, color: 'text-blue-400' },
    { label: 'Pending Review', value: stats.pending_approval ?? 0, color: 'text-yellow-400' },
    { label: 'Emails Today', value: stats.emails_today ?? 0, color: 'text-purple-400' },
    { label: 'Replies', value: stats.email_replies ?? 0, color: 'text-pink-400' },
  ]

  return (
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-8">
      {items.map(({ label, value, color }) => (
        <div key={label} className="flex flex-col">
          <span className={`text-xl font-bold ${color}`}>{value}</span>
          <span className="text-xs text-gray-500">{label}</span>
        </div>
      ))}
      {lastRefresh && (
        <div className="ml-auto text-xs text-gray-600">
          Updated {lastRefresh.toLocaleTimeString()}
        </div>
      )}
    </header>
  )
}
