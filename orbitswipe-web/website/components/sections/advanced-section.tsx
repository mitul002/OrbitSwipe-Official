"use client"

import { motion } from "framer-motion"
import { 
  Cpu, 
  Keyboard, 
  PanelLeft, 
  Monitor, 
  Clipboard, 
  Terminal 
} from "lucide-react"

const advancedFeatures = [
  {
    icon: Cpu,
    title: "Live System Stats",
    description: "CPU, RAM, Battery, Network",
  },
  {
    icon: Keyboard,
    title: "Global Hotkeys",
    description: "Fully customizable shortcuts",
  },
  {
    icon: PanelLeft,
    title: "Auto-hide Trigger",
    description: "Edge activation on hover",
  },
  {
    icon: Monitor,
    title: "Multi-monitor",
    description: "Works on any display",
  },
  {
    icon: Clipboard,
    title: "Clipboard Tools",
    description: "Quick access utilities",
  },
  {
    icon: Terminal,
    title: "Script Execution",
    description: "PowerShell, Python, Batch",
  },
]

export function AdvancedSection() {
  return (
    <section className="relative py-32 px-4 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-950/20 via-background to-violet-950/20" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-purple-600/10 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 rounded-full glass-card text-sm text-purple-300 mb-4">
            Advanced Features
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
              Power Under the Hood
            </span>
          </h2>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"
        >
          {advancedFeatures.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ scale: 1.05, y: -5 }}
              className="group"
            >
              <div className="relative p-6 rounded-2xl glass-card text-center h-full hover:border-purple-500/30 transition-all duration-300">
                {/* Glow effect */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/10 to-violet-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                
                <div className="relative">
                  <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-gradient-to-br from-purple-500/20 to-violet-500/20 flex items-center justify-center group-hover:from-purple-500/30 group-hover:to-violet-500/30 transition-all duration-300">
                    <feature.icon className="w-6 h-6 text-purple-400 group-hover:text-purple-300 transition-colors" />
                  </div>
                  <h3 className="font-semibold text-foreground text-sm mb-1 group-hover:text-purple-300 transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
