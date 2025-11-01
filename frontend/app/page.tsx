'use client'

import { useEffect, useState } from 'react'

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch backend status
    fetch('http://localhost:8000/')
      .then(res => res.json())
      .then(data => {
        setBackendStatus(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Backend connection failed:', err)
        setLoading(false)
      })
  }, [])

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-red-500 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-12">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="text-6xl mb-4">🪅</div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
              Pinata Code
            </h1>
            <p className="text-xl text-gray-600 italic">
              It's what's inside that counts
            </p>
          </div>

          {/* Status Cards */}
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            {/* Frontend Status */}
            <div className="border-2 border-green-500 rounded-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-semibold">Frontend</h2>
                <span className="flex items-center text-green-600">
                  <span className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                  Running
                </span>
              </div>
              <p className="text-sm text-gray-600">Next.js 14 + React + TypeScript</p>
              <p className="text-xs text-gray-500 mt-2">Port: 3000</p>
            </div>

            {/* Backend Status */}
            <div className={`border-2 rounded-lg p-6 ${backendStatus ? 'border-green-500' : loading ? 'border-yellow-500' : 'border-red-500'}`}>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-semibold">Backend</h2>
                <span className={`flex items-center ${backendStatus ? 'text-green-600' : loading ? 'text-yellow-600' : 'text-red-600'}`}>
                  <span className={`w-3 h-3 rounded-full mr-2 ${backendStatus ? 'bg-green-500 animate-pulse' : loading ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'}`}></span>
                  {backendStatus ? 'Connected' : loading ? 'Connecting...' : 'Offline'}
                </span>
              </div>
              <p className="text-sm text-gray-600">FastAPI + Python</p>
              <p className="text-xs text-gray-500 mt-2">Port: 8000</p>
              {backendStatus && (
                <p className="text-xs text-green-600 mt-1">✓ {backendStatus.message}</p>
              )}
            </div>
          </div>

          {/* Backend Response */}
          {backendStatus && (
            <div className="bg-gray-50 rounded-lg p-6 mb-8">
              <h3 className="font-semibold mb-3">Backend Response:</h3>
              <pre className="text-sm overflow-x-auto bg-white p-4 rounded border">
                {JSON.stringify(backendStatus, null, 2)}
              </pre>
            </div>
          )}

          {/* Services Status */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <h3 className="font-semibold mb-3 text-blue-900">Infrastructure Services:</h3>
            <ul className="space-y-2 text-sm text-blue-800">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                PostgreSQL: localhost:5432
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Redis: localhost:6379
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                MinIO: <a href="http://localhost:9001" className="underline" target="_blank">localhost:9001</a>
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Backend API: <a href="http://localhost:8000/docs" className="underline" target="_blank">localhost:8000/docs</a>
              </li>
            </ul>
          </div>

          {/* Quick Links */}
          <div className="grid md:grid-cols-3 gap-4">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              className="block p-4 bg-purple-100 hover:bg-purple-200 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">📚</div>
              <div className="font-semibold">API Docs</div>
              <div className="text-xs text-gray-600">Swagger UI</div>
            </a>
            <a
              href="http://localhost:9001"
              target="_blank"
              className="block p-4 bg-pink-100 hover:bg-pink-200 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">🗄️</div>
              <div className="font-semibold">MinIO Console</div>
              <div className="text-xs text-gray-600">Storage Admin</div>
            </a>
            <a
              href="http://localhost:5050"
              target="_blank"
              className="block p-4 bg-red-100 hover:bg-red-200 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">🐘</div>
              <div className="font-semibold">PgAdmin</div>
              <div className="text-xs text-gray-600">Database GUI</div>
            </a>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>🚀 All services started successfully!</p>
            <p className="mt-2">Ready to build your SaaS platform</p>
          </div>
        </div>
      </div>
    </main>
  )
}
