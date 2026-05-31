"use client"

import { motion } from "framer-motion"
import { 
  HardDrive, 
  Cpu, 
  Monitor, 
  Shield, 
  Zap, 
  Clock,
  Check
} from "lucide-react"

const specs = [
  { icon: HardDrive, label: "Format", value: "Portable" },
  { icon: Cpu, label: "CPU", value: "Minimal" },
  { icon: Monitor, label: "OS", value: "Win 10/11" },
  { icon: Shield, label: "No Ads", value: "Ever" },
  { icon: Zap, label: "Startup", value: "<1s" },
  { icon: Clock, label: "Offline", value: "100%" },
]

const requirements = [
  "Windows 10 or Windows 11 (64-bit)",
  "Fully Standalone Executable (No external runtimes required!)",
  "Minimal footprint: Zero installation required (Portable)",
  "Highly optimized: Works smoothly with minimal resources (4GB RAM suggested)",
  "No internet connection required after initial download",
]

export function SpecsSection() {
  return (
    <section id="requirements" className="relative py-32 px-4 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-purple-950/10 via-background to-background" />
        {/* Animated grid */}
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(124,58,237,0.8) 1px, transparent 0)`,
            backgroundSize: "40px 40px",
          }}
        />
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
            Technical Specifications
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-foreground">Lightweight &</span>{" "}
            <span className="bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
              Efficient
            </span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto text-pretty">
            Built for performance. No bloat, no telemetry, no background services draining your resources.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Stats Grid */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="grid grid-cols-3 gap-4"
          >
            {specs.map((spec, index) => (
              <motion.div
                key={spec.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                whileHover={{ scale: 1.05, y: -5 }}
                className="group"
              >
                <div className="relative aspect-square p-4 rounded-2xl glass-card flex flex-col items-center justify-center text-center hover:border-purple-500/40 transition-all duration-300">
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-500/10 to-violet-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <spec.icon className="w-8 h-8 text-purple-400 mb-3 group-hover:scale-110 transition-transform duration-300" />
                  <div className="text-2xl font-bold text-foreground mb-1">
                    {spec.value}
                  </div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wide">
                    {spec.label}
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Requirements List */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="glass-card rounded-2xl p-8"
          >
            <h3 className="text-xl font-bold text-foreground mb-6 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/20 to-violet-500/20 flex items-center justify-center">
                <Monitor className="w-5 h-5 text-purple-400" />
              </div>
              System Requirements
            </h3>
            <ul className="space-y-4">
              {requirements.map((req, index) => (
                <motion.li
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
                  className="flex items-center gap-3 text-muted-foreground"
                >
                  <div className="w-5 h-5 rounded-full bg-purple-500/20 flex items-center justify-center shrink-0">
                    <Check className="w-3 h-3 text-purple-400" />
                  </div>
                  {req}
                </motion.li>
              ))}
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
