import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import './globals.css'

const inter = Inter({ 
  subsets: ["latin"],
  variable: '--font-inter'
})

export const metadata: Metadata = {
  title: 'OrbitSwipe - Control Your PC in One Swipe',
  description: 'OrbitSwipe is a powerful radial launcher for Windows that brings your apps, system tools, and live stats into one stunning glass interface.',
  keywords: ['Windows', 'launcher', 'radial menu', 'productivity', 'glass UI', 'system tools'],
  authors: [{ name: 'Cross Tech' }],
  icons: {
    icon: '/orbitswipe-icon.ico',
  },
  openGraph: {
    title: 'OrbitSwipe - Control Your PC in One Swipe',
    description: 'A powerful radial launcher for Windows with glass UI and live system stats.',
    type: 'website',
  },
}

export const viewport: Viewport = {
  themeColor: '#7c3aed',
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="bg-background">
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
