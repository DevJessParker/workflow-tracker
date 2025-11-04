'use client'

interface PinataSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  message?: string
}

export default function PinataSpinner({ size = 'md', message }: PinataSpinnerProps) {
  const dimensions = {
    sm: { container: 64, dotSize: 8 },
    md: { container: 96, dotSize: 12 },
    lg: { container: 128, dotSize: 16 },
  }

  const pinataSize = {
    sm: 'text-2xl',
    md: 'text-4xl',
    lg: 'text-6xl',
  }

  const config = dimensions[size]
  const radius = config.container / 2 - config.dotSize
  const numDots = 8

  // ROY G BIV colors
  const colors = [
    '#E74C3C', // Red
    '#E67E22', // Orange
    '#F1C40F', // Yellow
    '#2ECC71', // Green
    '#3498DB', // Blue
    '#6C3483', // Indigo
    '#9B59B6', // Violet
    '#E91E63', // Magenta
  ]

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: config.container, height: config.container }}>
        {/* Circle of circles */}
        <div className="absolute inset-0 animate-spin">
          {Array.from({ length: numDots }).map((_, i) => {
            const angle = (i / numDots) * 2 * Math.PI
            const x = radius * Math.cos(angle) + config.container / 2 - config.dotSize / 2
            const y = radius * Math.sin(angle) + config.container / 2 - config.dotSize / 2

            return (
              <div
                key={i}
                className="absolute rounded-full"
                style={{
                  width: config.dotSize,
                  height: config.dotSize,
                  left: x,
                  top: y,
                  backgroundColor: colors[i % colors.length],
                  boxShadow: `0 0 ${config.dotSize / 2}px ${colors[i % colors.length]}`,
                }}
              />
            )
          })}
        </div>

        {/* Pinata in the center */}
        <div
          className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 ${pinataSize[size]}`}
          style={{ animation: 'bounce 1s infinite' }}
        >
          🪅
        </div>
      </div>

      {message && (
        <p className="mt-4 text-gray-600 font-medium animate-pulse">{message}</p>
      )}
    </div>
  )
}
