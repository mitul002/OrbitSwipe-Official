"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, HelpCircle } from "lucide-react"

const FAQS = [
  {
    q: "What is OrbitSwipe?",
    a: "OrbitSwipe is a modern radial launcher and system overlay utility for Windows. It allows you to access your favorite applications, monitor real-time system stats (CPU, RAM, Network, Battery), control media, and trigger system commands (Lock, Sleep, Volume) via a sleek, swipe-activated glass interface or a customizable hotkey."
  },
  {
    q: "Is OrbitSwipe safe to run on my Windows machine?",
    a: "Absolutely. OrbitSwipe runs entirely locally on your operating system. It does not monitor, collect, or upload your keystrokes, screen activity, or personal data. We value privacy and operate a strict offline-first utility model."
  },
  {
    q: "How does the 30-day trial work?",
    a: "You can download OrbitSwipe and experience all its premium features completely free for 30 days. No credit card or registration is required. Once the trial expires, you can purchase a Pro license key to permanently unlock the software."
  },
  {
    q: "Can I transfer my license key to a new PC?",
    a: "Yes. Your lifetime license key supports flexible device switching. You can easily deactivate your license key from the settings menu of the old machine, or request a license transfer if you no longer have access to your previous PC."
  },
  {
    q: "What is your refund policy?",
    a: "We offer a 14-day money-back guarantee. If OrbitSwipe fails to function properly on your Windows machine, or if you face technical issues that we cannot resolve, you are eligible for a full refund within 14 days of your purchase."
  }
]

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <section id="faq" className="relative py-32 px-4 overflow-hidden">
      {/* Background gradients */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 right-1/4 w-[500px] h-[500px] bg-purple-600/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/3 left-1/4 w-[500px] h-[500px] bg-violet-600/5 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium mb-4">
            Got Questions?
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-white">Frequently Asked </span>
            <span className="bg-gradient-to-r from-purple-400 via-violet-400 to-purple-500 bg-clip-text text-transparent">
              Questions
            </span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Everything you need to know about OrbitSwipe features, safety, licensing, and billing.
          </p>
        </motion.div>

        {/* Accordion Grid */}
        <div className="space-y-4">
          {FAQS.map((faq, index) => {
            const isOpen = openIndex === index
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`rounded-2xl border transition-all duration-300 ${
                  isOpen
                    ? "bg-purple-950/10 border-purple-500/35 shadow-lg shadow-purple-500/5"
                    : "glass-card border-white/5 bg-white/[0.01] hover:border-white/10 hover:bg-white/[0.02]"
                }`}
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : index)}
                  className="w-full flex items-center justify-between p-6 text-left cursor-pointer"
                >
                  <div className="flex items-center gap-4 pr-4">
                    <HelpCircle className={`w-5 h-5 shrink-0 transition-colors ${isOpen ? "text-purple-400" : "text-muted-foreground"}`} />
                    <span className="font-semibold text-white/90 text-base md:text-lg">
                      {faq.q}
                    </span>
                  </div>
                  <motion.div
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                    className="text-muted-foreground shrink-0"
                  >
                    <ChevronDown className="w-5 h-5" />
                  </motion.div>
                </button>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: "easeInOut" }}
                      className="overflow-hidden"
                    >
                      <div className="p-6 pt-0 border-t border-white/5 text-muted-foreground text-sm md:text-base leading-relaxed text-pretty">
                        {faq.a}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
