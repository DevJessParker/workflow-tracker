'use client'

import { useEffect, useRef, useState } from 'react'

interface MermaidDiagramProps {
  chart: string
  className?: string
}

export default function MermaidDiagram({ chart, className = '' }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || !chart) return

      try {
        setIsLoading(true)
        setError(null)

        // Dynamic import of mermaid to avoid SSR issues
        const mermaid = (await import('mermaid')).default

        // Initialize mermaid with configuration
        mermaid.initialize({
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose',
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: 'basis',
          },
        })

        // Generate unique ID for this diagram
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`

        // Clear previous content
        containerRef.current.innerHTML = ''

        // Render the diagram
        const { svg } = await mermaid.render(id, chart)

        // Insert the SVG
        if (containerRef.current) {
          containerRef.current.innerHTML = svg
        }

        setIsLoading(false)
      } catch (err) {
        console.error('Mermaid rendering error:', err)
        setError(err instanceof Error ? err.message : 'Failed to render diagram')
        setIsLoading(false)
      }
    }

    renderDiagram()
  }, [chart])

  if (error) {
    return (
      <div className={`p-4 bg-red-50 border border-red-200 rounded-lg ${className}`}>
        <p className="text-red-700 font-semibold">Failed to render diagram</p>
        <p className="text-red-600 text-sm mt-2">{error}</p>
        <details className="mt-3">
          <summary className="text-red-600 text-sm cursor-pointer">Show diagram source</summary>
          <pre className="mt-2 p-2 bg-red-100 rounded text-xs overflow-auto">
            {chart}
          </pre>
        </details>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 bg-gray-50 rounded-lg ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Rendering diagram...</span>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`mermaid-container overflow-auto ${className}`}
      style={{ maxWidth: '100%' }}
    />
  )
}
