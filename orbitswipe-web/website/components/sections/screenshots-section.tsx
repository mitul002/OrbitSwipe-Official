"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Monitor, Cpu, Radio, Palette, Layers, Power } from "lucide-react"

const SCREENSHOTS = [
  {
    id: "wintop",
    title: "WinTop Manager",
    subtitle: "Stealth Always-On-Top Utility",
    image: "/wintop manager.png",
    icon: Radio,
    color: "#10b981",
    desc: "Keep critical workspace tools or references strictly on top. Replicating Windows PowerToys WinTop, pin any active application window instantly as 'Always on Top' using customizable keyboard hotkeys.",
    highlights: ["Stealth Alt-Pulse key triggers", "Always-on-top viewport pin lock", "Instant window layer elevation", "Lightweight PyQt6 performance thread"],
  },
  {
    id: "doublering",
    title: "Center Display Switcher",
    subtitle: "Mode 1 / Mode 2 Hub Toggle",
    image: "/center display mode.png",
    icon: Layers,
    color: "#38bdf8",
    desc: "Toggle seamlessly inside the center display panel. Reassert hardware metrics or active browser-based Chrome media playbacks without ever disrupting your current workspace.",
    highlights: ["Mode 1 / Mode 2 hub switching", "Clock & hardware metrics", "Play, pause & seek track control", "Custom digital clock widgets"],
  },
  {
    id: "custom",
    title: "Theme Changer",
    subtitle: "10 Presets & Auto Wallpaper Sync",
    image: "/theme settings.png",
    icon: Palette,
    color: "#fb923c",
    desc: "Inject perfect visual harmony to match your desktop wallpaper. Fully customize transparent glass background color filters, opacity coefficients, and glowing border frame presets.",
    highlights: ["10 designer glass presets", "Dynamic Auto-Wallpaper sync", "Custom color overlay adjustments", "Vibrant neon border light glows"],
  },
  {
    id: "mode1",
    title: "Mode 1 Launcher",
    subtitle: "Concentric Spacing",
    image: "/mode1.png",
    icon: Monitor,
    color: "#a78bfa",
    desc: "Experience the ultimate symmetrical layout in Mode 1. Features robust concentric inner and outer tracks centered flat against your desktop sidebar edge.",
    highlights: ["Symmetrical circular spacing", "Perfect flat-anchored edge", "Lag-free Windows hook", "Glassmorphic preset overlays"],
  },
  {
    id: "mode2",
    title: "Mode 2 Launcher",
    subtitle: "System Stats & Active Hub",
    image: "/mode 2.png",
    icon: Cpu,
    color: "#c084fc",
    desc: "Unlock real-time telemetry tracking in Mode 2. Directly track active memory capacity, processor utilization thresholds, battery charge states, and local network traffic speeds.",
    highlights: ["Interactive center telemetry dial", "Processor utilization speeds", "Battery rates & levels", "Stealth process logging"],
  },
  {
    id: "power",
    title: "Power Manager",
    subtitle: "Scheduled Actions Overlay",
    image: "/power menu.png",
    icon: Power,
    color: "#a78bfa",
    desc: "Shut down, restart, hibernate, sleep, or lock your computer instantly or on a custom schedule. Keep tracking time in the background with a clean visual countdown timer widget.",
    highlights: ["Scheduled shutdown & restart", "Background countdown tracker", "Instant one-click trigger", "Sleek glassmorphic countdown HUD"],
  },
]

export function ScreenshotsSection() {
  const [activeTab, setActiveTab] = useState(0)
  const current = SCREENSHOTS[activeTab]
  const Icon = current.icon

  return (
    <section id="screenshots" className="relative py-24 px-4 overflow-hidden">
      {/* Subtle grid accent */}
      <div 
        className="absolute inset-0 opacity-5 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle, rgba(167,139,250,0.15) 1px, transparent 1.5px)`,
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto">
        
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold uppercase tracking-wider mb-4">
            Product Showcase
          </span>
          <h2 className="text-4xl md:text-5xl font-extrabold mb-4 text-white">
            Actual Launcher{" "}
            <span className="bg-gradient-to-r from-purple-400 via-violet-300 to-purple-500 bg-clip-text text-transparent">
              UI
            </span>
          </h2>
          <p className="text-purple-200/50 max-w-2xl mx-auto font-light text-base">
            Take a look at the real high-fidelity WPF Fluent interface running live on Windows 10/11.
          </p>
        </motion.div>

        {/* Dynamic Navigation Tabs */}
        <div className="flex flex-wrap justify-center gap-3 mb-12">
          {SCREENSHOTS.map((screen, idx) => {
            const isActive = activeTab === idx
            const TabIcon = screen.icon
            return (
              <button
                key={screen.id}
                onClick={() => setActiveTab(idx)}
                className={`flex items-center gap-2 px-5 py-3 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 border ${
                  isActive 
                    ? "text-white shadow-lg" 
                    : "text-purple-300/60 border-white/5 bg-slate-900/30 hover:border-purple-500/20 hover:text-purple-300"
                }`}
                style={{
                  backgroundColor: isActive ? `${screen.color}20` : "transparent",
                  borderColor: isActive ? screen.color : "transparent",
                  boxShadow: isActive ? `0 0 20px ${screen.color}30` : "none",
                }}
              >
                <TabIcon className="w-4 h-4 shrink-0" style={{ color: screen.color }} />
                <span>{screen.title}</span>
              </button>
            )
          })}
        </div>

        {/* Large Layout Presentation Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: High-Fidelity Screenshot Image */}
          <div className="lg:col-span-6 w-full flex justify-center">
            <div className="relative w-full max-w-[310px] group">
              {/* Animated backdrop light behind screenshot */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={current.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.35 }}
                  exit={{ opacity: 0 }}
                  className="absolute -inset-2 rounded-[32px] blur-2xl transition duration-500 pointer-events-none"
                  style={{ background: current.color }}
                />
              </AnimatePresence>

              {/* Screenshot frame */}
              <div className="relative rounded-[32px] p-2 bg-slate-950/70 border border-white/10 backdrop-blur-2xl shadow-2xl overflow-hidden">
                <AnimatePresence mode="wait">
                  <motion.img
                    key={current.id}
                    src={current.image}
                    alt={current.title}
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.98 }}
                    transition={{ duration: 0.4 }}
                    className="w-full rounded-[24px] border border-white/5 select-none shadow-inner"
                  />
                </AnimatePresence>
              </div>
            </div>
          </div>

          {/* Right Column: Detailed Screenshot Specification */}
          <div className="lg:col-span-6 flex flex-col justify-center items-start text-left">
            <AnimatePresence mode="wait">
              <motion.div
                key={current.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.4 }}
                className="w-full"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div 
                    className="p-3 rounded-2xl border"
                    style={{ 
                      backgroundColor: `${current.color}15`, 
                      borderColor: `${current.color}35` 
                    }}
                  >
                    <Icon className="w-6 h-6" style={{ color: current.color }} />
                  </div>
                  <div>
                    <h3 className="text-2xl font-extrabold text-white">{current.title}</h3>
                    <p className="text-xs uppercase tracking-wider font-bold" style={{ color: current.color }}>
                      {current.subtitle}
                    </p>
                  </div>
                </div>

                <p className="text-purple-200/70 text-sm leading-relaxed mb-8 font-light">
                  {current.desc}
                </p>

                {/* Highlights List */}
                <div className="space-y-3">
                  <span className="text-[10px] uppercase tracking-widest font-extrabold text-purple-300/40">
                    Feature Highlights
                  </span>
                  {current.highlights.map((highlight, idx) => (
                    <div key={idx} className="flex items-center gap-2.5 text-xs text-purple-200/80 font-medium">
                      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: current.color }} />
                      <span>{highlight}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

        </div>

      </div>
    </section>
  )
}
