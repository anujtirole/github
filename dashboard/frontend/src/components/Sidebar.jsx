export default function Sidebar({ view, setView, counts }) {
  const items = [
    { key: 'pending', label: 'Pending', count: counts.pending, color: 'text-yellow-400' },
    { key: 'emails', label: 'Emails', count: counts.emails, color: 'text-blue-400' },
    { key: 'applied', label: 'Applied', count: counts.applied, color: 'text-green-400' },
    { key: 'failed', label: 'Failed', count: counts.failed, color: 'text-red-400' },
  ]

  return (
    <aside className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="px-5 py-4 border-b border-gray-800">
        <h1 className="text-lg font-bold text-indigo-400 tracking-tight">JobHunterX</h1>
        <p className="text-xs text-gray-500 mt-0.5">Autonomous AI Job Hunter</p>
      </div>
      <nav className="flex-1 py-4 px-2">
        {items.map(({ key, label, count, color }) => (
          <button
            key={key}
            onClick={() => setView(key)}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors ${
              view === key
                ? 'bg-indigo-600 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
            }`}
          >
            <span>{label}</span>
            <span className={`font-semibold ${view === key ? 'text-white' : color}`}>
              {count}
            </span>
          </button>
        ))}
      </nav>
      <div className="px-4 py-3 border-t border-gray-800">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          <span className="text-xs text-gray-400">System Live</span>
        </div>
      </div>
    </aside>
  )
}
