'use client'

import { useEffect, useState } from 'react'

interface ConfettiExplosionProps {
  onComplete?: () => void
}

export default function ConfettiExplosion({ onComplete }: ConfettiExplosionProps) {
  const [confettiPieces, setConfettiPieces] = useState<Array<{
    id: number
    left: number
    color: string
    delay: number
    duration: number
    rotation: number
  }>>([])

  useEffect(() => {
    // Generate 50 confetti pieces with random properties
    const pieces = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: Math.random() * 100, // Random horizontal position (%)
      color: [
        '#667eea', '#764ba2', '#f093fb', '#f5576c',
        '#feca57', '#48dbfb', '#0abde3', '#00d2d3',
        '#ee5a6f', '#c471ed', '#f7b731'
      ][Math.floor(Math.random() * 11)],
      delay: Math.random() * 0.3, // Random delay (0-0.3s)
      duration: 1.5 + Math.random() * 1, // Random duration (1.5-2.5s)
      rotation: Math.random() * 720 - 360, // Random rotation (-360 to 360 degrees)
    }))

    setConfettiPieces(pieces)

    // Call onComplete after animation finishes
    if (onComplete) {
      setTimeout(onComplete, 2500)
    }
  }, [onComplete])

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {confettiPieces.map((piece) => (
        <div
          key={piece.id}
          className="absolute"
          style={{
            left: `${piece.left}%`,
            top: '-10px',
            animation: `confettiFall ${piece.duration}s ease-in ${piece.delay}s forwards`,
            width: '10px',
            height: '10px',
            backgroundColor: piece.color,
            transform: `rotate(${piece.rotation}deg)`,
          }}
        />
      ))}

      <style jsx>{`
        @keyframes confettiFall {
          0% {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh) rotate(${720}deg);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  )
}
