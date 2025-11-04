'use client'

interface PinataSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  message?: string
}

export default function PinataSpinner({ size = 'md', message }: PinataSpinnerProps) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
  }

  const pinataSize = {
    sm: 'text-2xl',
    md: 'text-4xl',
    lg: 'text-6xl',
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative">
        {/* Rainbow spinning ring */}
        <div
          className={`${sizeClasses[size]} rounded-full animate-spin`}
          style={{
            background: 'conic-gradient(from 0deg, #667eea, #764ba2, #f093fb, #f5576c, #feca57, #48dbfb, #0abde3, #00d2d3, #667eea)',
            padding: '3px',
          }}
        >
          <div className="w-full h-full bg-white rounded-full"></div>
        </div>

        {/* Pinata in the center */}
        <div
          className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 ${pinataSize[size]} animate-bounce`}
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
