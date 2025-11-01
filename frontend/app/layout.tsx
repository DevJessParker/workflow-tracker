import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Pinata Code',
  description: "It's what's inside that counts - Code Workflow Analysis SaaS",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
