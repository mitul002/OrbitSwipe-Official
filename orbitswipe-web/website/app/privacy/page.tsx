import type { Metadata } from 'next'
import { Navbar } from "@/components/sections/navbar"
import { Footer } from "@/components/sections/footer"
import { ArrowLeft, Shield } from "lucide-react"
import Link from "next/link"

export const metadata: Metadata = {
  title: 'Privacy Policy - OrbitSwipe',
  description: 'Learn about how OrbitSwipe handles your privacy and data security.',
}

export default function PrivacyPolicy() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-32 pb-20 px-4 relative overflow-hidden">
        {/* Background Gradients */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-purple-600/10 rounded-full blur-[120px]" />
          <div className="absolute bottom-0 inset-0 bg-background" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto">
          {/* Back Button */}
          <Link 
            href="/"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-purple-400 transition-colors mb-8 group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Back to Home
          </Link>

          {/* Page Header */}
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-4xl font-extrabold bg-gradient-to-r from-white via-purple-100 to-purple-400 bg-clip-text text-transparent">
                Privacy Policy
              </h1>
              <p className="text-sm text-muted-foreground mt-1">Last updated: May 2026</p>
            </div>
          </div>

          {/* Content Card */}
          <div className="glass-card p-8 md:p-10 rounded-3xl border border-white/5 bg-white/[0.02] backdrop-blur-xl space-y-8 text-muted-foreground leading-relaxed">
            <p className="text-foreground/90 font-medium">
              At OrbitSwipe, accessible from{' '}
              <a href="https://orbitswipe.vercel.app/" className="text-purple-400 hover:underline">
                https://orbitswipe.vercel.app/
              </a>
              , one of our main priorities is the privacy of our visitors and users. This Privacy Policy document contains types of information that is collected and recorded by OrbitSwipe and how we use it.
            </p>

            <div className="border-t border-white/5 pt-8 space-y-4">
              <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                <span className="text-purple-500">1.</span> Information We Collect
              </h2>
              <p>
                We only collect minimal information required to fulfill your software license. This includes:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>
                  <strong className="text-foreground/90">Email Address</strong> (provided during checkout via Lemon Squeezy to send your license key).
                </li>
                <li>
                  <strong className="text-foreground/90">Basic Device Information</strong> (non-personal hardware identifier used strictly to validate your automated license key usage).
                </li>
              </ul>
              <p className="bg-purple-950/20 border border-purple-500/20 rounded-xl p-4 text-purple-200 mt-4">
                We <strong className="text-white font-semibold">DO NOT</strong> track, collect, or store your personal data, desktop activity, or keystrokes. OrbitSwipe operates entirely locally on your machine.
              </p>
            </div>

            <div className="border-t border-white/5 pt-8 space-y-4">
              <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                <span className="text-purple-500">2.</span> Third-Party Services
              </h2>
              <p>
                We use Lemon Squeezy as our Merchant of Record for processing payments and managing license fulfillment. They collect billing information in accordance with their own strict privacy regulations.
              </p>
            </div>

            <div className="border-t border-white/5 pt-8 space-y-4">
              <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                <span className="text-purple-500">3.</span> Data Security
              </h2>
              <p>
                We take data security seriously. We implement industry-standard measures to protect any local configuration data and prevent unauthorized access to your application settings.
              </p>
            </div>

            <div className="border-t border-white/5 pt-8 space-y-4">
              <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                <span className="text-purple-500">4.</span> Contact Us
              </h2>
              <p>
                If you have any questions or concerns regarding our privacy practices, please feel free to contact us via email at{' '}
                <a href="mailto:hasinalmasmitul@gmail.com" className="text-purple-400 hover:underline">
                  hasinalmasmitul@gmail.com
                </a>.
              </p>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  )
}
