"use client"

import { motion } from "framer-motion"
import { Download, Zap, Wifi, Shield, Check, Sparkles, HardDrive, Monitor, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"

const benefits = [
  { icon: Sparkles, label: "WinTop Manager" },
  { icon: Zap, label: "Lightweight" },
  { icon: Wifi, label: "Fully Offline" },
  { icon: Shield, label: "No Bloat" },
  { icon: Monitor, label: "Win 10/11" },
  { icon: Clock, label: "Instant Start" },
]

const features = [
  "Radial launcher with glass UI",
  "WinTop window manager",
  "Live system stats",
  "Volume & brightness sliders",
  "Smart search",
  "Custom Glass Accents & Themes",
  "Workspace groups",
  "Global hotkeys",
]

export function DownloadSection() {
  return (
    <section id="download" className="relative py-32 px-4 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-background via-purple-950/20 to-background" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-purple-600/10 rounded-full blur-[200px]" />
        
        {/* Animated rings */}
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full border border-purple-500/10"
          animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.5, 0.3] }}
          transition={{ duration: 4, repeat: Infinity }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full border border-purple-500/5"
          animate={{ scale: [1.1, 1, 1.1], opacity: [0.2, 0.4, 0.2] }}
          transition={{ duration: 5, repeat: Infinity }}
        />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full glass-card text-sm text-purple-300 mb-8"
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span>Ready to Download</span>
          </motion.div>

          {/* Headline */}
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            <span className="text-foreground">Upgrade Your</span>
            <br />
            <span className="bg-gradient-to-r from-purple-400 via-violet-400 to-purple-500 bg-clip-text text-transparent">
              Windows Experience
            </span>
          </h2>

          {/* Subtext */}
          <p className="text-lg text-muted-foreground mb-10 max-w-xl mx-auto text-pretty">
            Join thousands of users who have transformed how they interact with Windows.
          </p>

          {/* Benefits row */}
          <div className="flex flex-wrap justify-center gap-6 mb-12">
            {benefits.map((benefit, index) => (
              <motion.div
                key={benefit.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="flex items-center gap-2 px-4 py-2 rounded-full glass-card"
              >
                <benefit.icon className="w-4 h-4 text-purple-400" />
                <span className="text-sm text-muted-foreground">{benefit.label}</span>
              </motion.div>
            ))}
          </div>

          {/* Main download card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative max-w-2xl mx-auto p-6 sm:p-12 rounded-3xl glass-card border-purple-500/20 overflow-hidden"
          >
            {/* Background glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-transparent to-violet-500/10 pointer-events-none" />
            
            {/* Feature list */}
            <div className="relative grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4 mb-10 text-left">
              {features.map((feature, index) => (
                <motion.div
                  key={feature}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: 0.3 + index * 0.05 }}
                  className="flex items-center gap-3"
                >
                  <div className="w-5 h-5 rounded-full bg-purple-500/20 flex items-center justify-center shrink-0">
                    <Check className="w-3 h-3 text-purple-400" />
                  </div>
                  <span className="text-sm sm:text-base text-muted-foreground">{feature}</span>
                </motion.div>
              ))}
            </div>

            {/* CTA Button */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.5 }}
            >
              <Button 
                size="lg" 
                className="relative group w-full sm:w-auto h-16 sm:h-20 px-8 sm:px-12 text-lg sm:text-xl bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500 border-0 transition-all duration-300 overflow-hidden"
                asChild
              >
                <a href="/OrbitSwipe.exe" download className="flex items-center justify-center gap-3 w-full h-full">
                  {/* Shine effect */}
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                    animate={{ x: ["-100%", "100%"] }}
                    transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                  />
                  <Download className="w-6 h-6 relative z-10 shrink-0" />
                  <span className="relative z-10 font-bold">Download OrbitSwipe</span>
                  <span className="text-sm opacity-75 font-normal relative z-10 shrink-0">v1.5.2</span>
                </a>
              </Button>
            </motion.div>

            {/* Version info */}
            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.6 }}
              className="mt-6 text-sm text-muted-foreground"
            >
              Windows 10/11 • 64-bit • Easy install
            </motion.p>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
