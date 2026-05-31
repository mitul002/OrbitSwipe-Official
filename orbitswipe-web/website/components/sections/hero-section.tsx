"use client"

import { useEffect, useState, useRef } from "react"
import { motion, AnimatePresence, useMotionValue, useSpring } from "framer-motion"
import { Download, Play, ChevronDown, Sparkles, ArrowRight, Layers, Monitor, Cpu, Radio, Palette } from "lucide-react"
import { Button } from "@/components/ui/button"

const glassPresets = [
  { name: "Dark Obsidian", accent: "#7c3aed", bg: "rgba(10, 10, 20, 0.85)", border: "#4c1d95" },
  { name: "Pure Crystal", accent: "#c4b5fd", bg: "rgba(200, 200, 240, 0.35)", border: "#e9d5ff" },
  { name: "Vibrant Glass", accent: "#c084fc", bg: "rgba(124, 58, 237, 0.45)", border: "#ddd6fe" },
  { name: "Pure Ghost", accent: "#ffffff", bg: "rgba(255, 255, 255, 0.05)", border: "rgba(255, 255, 255, 0.15)" },
  { name: "Neon Night", accent: "#c084fc", bg: "rgba(10, 10, 35, 0.85)", border: "#a78bfa" },
  { name: "Arctic Aura", accent: "#38bdf8", bg: "rgba(180, 230, 255, 0.4)", border: "#bae6fd" },
  { name: "Obsidian Sky", accent: "#f43f5e", bg: "rgba(25, 10, 45, 0.85)", border: "#fda4af" },
  { name: "Emerald Mist", accent: "#10b981", bg: "rgba(150, 255, 200, 0.45)", border: "#a7f3d0" },
  { name: "Dynamic Glass", accent: "#a855f7", bg: "rgba(88, 28, 135, 0.6)", border: "#e9d5ff" },
  { name: "Custom Glass", accent: "#fb923c", bg: "rgba(154, 52, 18, 0.6)", border: "#fdba74" },
]

const RECENTS_ITEMS = [
  // Inner ring items (exactly 18 items - heavily filled to eliminate any gaps!)
  { emoji: "📁", label: "Explorer" },
  { emoji: "📊", label: "Task Mgr" },
  { emoji: "💻", label: "Command" },
  { emoji: "🎨", label: "Paint" },
  { emoji: "⚙️", label: "Settings" },
  { emoji: "🌐", label: "Browser" },
  { emoji: "🧮", label: "Calculator" },
  { emoji: "📝", label: "Notepad" },
  { emoji: "🧹", label: "Disk Clean" },
  { emoji: "🔒", label: "Lock" },
  { emoji: "🔵", label: "Chrome" },
  { emoji: "🎛️", label: "Control Panel" },
  { emoji: "📦", label: "App List" },
  { emoji: "🔍", label: "Search" },
  { emoji: "📅", label: "Calendar" },
  { emoji: "⏱️", label: "Stopwatch" },
  { emoji: "🔄", label: "Update" },
  { emoji: "📸", label: "Screenshot" },
  // Outer ring items (exactly 22 items - massive abundance as requested!)
  { emoji: "📜", label: "Run Script" },
  { emoji: "🎮", label: "Game Mode" },
  { emoji: "🔑", label: "Registry" },
  { emoji: "📟", label: "Terminal" },
  { emoji: "🔊", label: "Sound" },
  { emoji: "🖥️", label: "Display" },
  { emoji: "🌐", label: "Web Search" },
  { emoji: "🎵", label: "Music Center" },
  { emoji: "📁", label: "Downloads" },
  { emoji: "💬", label: "Discord" },
  { emoji: "📧", label: "Mail App" },
  { emoji: "🎥", label: "OBS Studio" },
  { emoji: "🎨", label: "Photoshop" },
  { emoji: "🎮", label: "Steam" },
  { emoji: "📝", label: "VS Code" },
  { emoji: "🟢", label: "Spotify" },
  { emoji: "✈️", label: "Telegram" },
  { emoji: "🐙", label: "GitHub" },
  { emoji: "📊", label: "Excel" },
  { emoji: "📝", label: "Word" },
  { emoji: "💡", label: "Tips" },
  { emoji: "🔋", label: "Battery Info" },
  { emoji: "🔌", label: "Power Shell" },
  { emoji: "💾", label: "Backups" },
]

const FAVORITES_ITEMS = [
  // Inner ring items (exactly 18 - enriched to pack the inner ring perfectly!)
  { emoji: "📁", label: "Explorer" },
  { emoji: "📊", label: "Task Mgr" },
  { emoji: "🌙", label: "Bright -" },
  { emoji: "☀️", label: "Bright +" },
  { emoji: "🔇", label: "Mute" },
  { emoji: "🔉", label: "Volume -" },
  { emoji: "🔊", label: "Volume +" },
  { emoji: "🧹", label: "Disk Clean" },
  { emoji: "🔒", label: "Lock" },
  { emoji: "📦", label: "App List" },
  { emoji: "🔄", label: "Update" },
  { emoji: "🎨", label: "Paint" },
  { emoji: "💻", label: "Command" },
  { emoji: "📋", label: "Clipboard" },
  { emoji: "🔵", label: "Bluetooth" },
  { emoji: "📶", label: "WiFi" },
  { emoji: "📸", label: "Screenshot" },
  { emoji: "📜", label: "Run Script" },
  // Outer ring items (exactly 22 items - 4 more outer icons added!)
  { emoji: "🎛️", label: "Control Panel" },
  { emoji: "🎮", label: "Game Mode" },
  { emoji: "🔵", label: "Chrome" },
  { emoji: "📝", label: "Notepad" },
  { emoji: "🔑", label: "Registry" },
  { emoji: "📟", label: "Terminal" },
  { emoji: "🌐", label: "Web Search" },
  { emoji: "🎵", label: "Music Center" },
  { emoji: "📁", label: "Downloads" },
  { emoji: "💬", label: "Discord" },
  { emoji: "📧", label: "Mail App" },
  { emoji: "🎥", label: "OBS Studio" },
  { emoji: "🎨", label: "Photoshop" },
  { emoji: "🎮", label: "Steam" },
  { emoji: "📝", label: "VS Code" },
  { emoji: "🟢", label: "Spotify" },
  { emoji: "✈️", label: "Telegram" },
  { emoji: "🐙", label: "GitHub" },
  { emoji: "📊", label: "Excel" },
  { emoji: "📝", label: "Word" },
  { emoji: "💡", label: "Tips" },
  { emoji: "🔋", label: "Battery Info" },
]

const TOOLBOX_ITEMS = [
  // Inner ring items (exactly 18 - enriched to pack the inner ring perfectly!)
  { emoji: "📁", label: "Explorer" },
  { emoji: "📊", label: "Task Mgr" },
  { emoji: "⚙️", label: "Settings" },
  { emoji: "📅", label: "Time/Date" },
  { emoji: "🖥️", label: "Display" },
  { emoji: "🔊", label: "Sound" },
  { emoji: "📶", label: "Network" },
  { emoji: "🎛️", label: "Control Panel" },
  { emoji: "🧹", label: "Disk Clean" },
  { emoji: "🔒", label: "Lock" },
  { emoji: "📦", label: "App List" },
  { emoji: "🔄", label: "Update" },
  { emoji: "🎨", label: "Paint" },
  { emoji: "💻", label: "Command" },
  { emoji: "📋", label: "Clipboard" },
  { emoji: "🔵", label: "Bluetooth" },
  { emoji: "📶", label: "WiFi" },
  { emoji: "📸", label: "Screenshot" },
  // Outer ring items (exactly 22 items - 4 more outer icons added!)
  { emoji: "📜", label: "Run Script" },
  { emoji: "📝", label: "Notepad" },
  { emoji: "🔑", label: "Registry" },
  { emoji: "⚙️", label: "Services" },
  { emoji: "📟", label: "Terminal" },
  { emoji: "ℹ️", label: "Sys Info" },
  { emoji: "🎮", label: "Game Mode" },
  { emoji: "🔵", label: "Chrome" },
  { emoji: "📁", label: "Documents" },
  { emoji: "🔌", label: "Power Shell" },
  { emoji: "💾", label: "Backups" },
  { emoji: "🛡️", label: "Firewall" },
  { emoji: "🧩", label: "Extensions" },
  { emoji: "💡", label: "Quick Tips" },
  { emoji: "🌐", label: "DNS Tool" },
  { emoji: "📊", label: "Analyzer" },
  { emoji: "🎨", label: "Vector" },
  { emoji: "📁", label: "Temp Files" },
  { emoji: "💡", label: "Tips" },
  { emoji: "🔋", label: "Battery Info" },
  { emoji: "💬", label: "Discord" },
  { emoji: "📧", label: "Mail App" },
]

const TABS = ["Recents", "Favorites", "Toolbox"]

function ParticleField() {
  const [particles, setParticles] = useState<Array<{ x: number; y: number; scale: number; delay: number }>>([])

  useEffect(() => {
    setParticles(
      [...Array(30)].map(() => ({
        x: Math.random() * 100,
        y: Math.random() * 100,
        scale: Math.random() * 0.5 + 0.5,
        delay: Math.random() * 5,
      }))
    )
  }, [])

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((particle, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-purple-500/30 rounded-full"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
          }}
          animate={{
            y: [0, -100, -200],
            opacity: [0, 1, 0],
            scale: [particle.scale, particle.scale * 1.5, particle.scale],
          }}
          transition={{
            duration: 12 + Math.random() * 12,
            repeat: Infinity,
            delay: particle.delay,
            ease: "linear",
          }}
        />
      ))}
    </div>
  )
}

function FloatingOrbs() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      <motion.div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px]"
        animate={{ rotate: 360 }}
        transition={{ duration: 80, repeat: Infinity, ease: "linear" }}
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-36 h-36 bg-purple-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-48 bg-violet-600/10 rounded-full blur-3xl" />
      </motion.div>
      <motion.div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(124,58,237,0.1) 0%, transparent 70%)",
        }}
        animate={{
          scale: [1, 1.15, 1],
          opacity: [0.4, 0.6, 0.4],
        }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  )
}

function InteractiveGlow() {
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  const springConfig = { damping: 30, stiffness: 120 }
  const x = useSpring(mouseX, springConfig)
  const y = useSpring(mouseY, springConfig)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseX.set(e.clientX)
      mouseY.set(e.clientY)
    }
    window.addEventListener("mousemove", handleMouseMove)
    return () => window.removeEventListener("mousemove", handleMouseMove)
  }, [mouseX, mouseY])

  return (
    <motion.div
      className="fixed w-[500px] h-[500px] pointer-events-none z-0 opacity-20"
      style={{
        x,
        y,
        translateX: "-50%",
        translateY: "-50%",
        background: "radial-gradient(circle, rgba(124,58,237,0.15) 0%, transparent 70%)",
      }}
    />
  )
}

export function HeroSection() {
  const [selectedPreset, setSelectedPreset] = useState(0)
  const [isExpanded, setIsExpanded] = useState(true)
  const [activeTab, setActiveTab] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [hubMode, setHubMode] = useState<"stats" | "media">("stats")
  const [hoveredItem, setHoveredItem] = useState<string | null>(null)
  const [time, setTime] = useState({ hour: "10", minute: "43", period: "PM" })
  
  const preset = glassPresets[selectedPreset]
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      setTime({
        hour: (now.getHours() % 12 || 12).toString().padStart(2, "0"),
        minute: now.getMinutes().toString().padStart(2, "0"),
        period: now.getHours() >= 12 ? "PM" : "AM"
      })
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // Rotate icons smoothly using scroll wheel and touch drag intercepters
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleWheelPrevent = (e: WheelEvent) => {
      e.preventDefault()
      const speed = 0.08
      const step = e.deltaY * speed
      setRotation(prev => (prev + step + 360) % 360)
    }

    let startY = 0

    const handleTouchStart = (e: TouchEvent) => {
      startY = e.touches[0].clientY
    }

    const handleTouchMove = (e: TouchEvent) => {
      if (startY === 0) return
      const currentY = e.touches[0].clientY
      const deltaY = currentY - startY
      
      if (isExpanded) {
        e.preventDefault() // prevent standard page scroll when interacting with active dial
      }
      
      const speed = 0.45 // touch sensitivity
      setRotation(prev => (prev - deltaY * speed + 360) % 360)
      startY = currentY
    }

    const handleTouchEnd = () => {
      startY = 0
    }

    container.addEventListener("wheel", handleWheelPrevent, { passive: false })
    container.addEventListener("touchstart", handleTouchStart, { passive: true })
    container.addEventListener("touchmove", handleTouchMove, { passive: false })
    container.addEventListener("touchend", handleTouchEnd, { passive: true })

    return () => {
      container.removeEventListener("wheel", handleWheelPrevent)
      container.removeEventListener("touchstart", handleTouchStart)
      container.removeEventListener("touchmove", handleTouchMove)
      container.removeEventListener("touchend", handleTouchEnd)
    }
  }, [isExpanded])

  const getTabItems = () => {
    switch (activeTab) {
      case 0: return RECENTS_ITEMS
      case 1: return FAVORITES_ITEMS
      case 2: return TOOLBOX_ITEMS
      default: return FAVORITES_ITEMS
    }
  }

  const tabItems = getTabItems()
  const innerLimit = 18
  const innerItems = tabItems.slice(0, innerLimit)
  const outerItems = tabItems.slice(innerLimit)

  // All coordinates rounded to 2dp to prevent SSR/CSR hydration mismatch
  const rd = (v: number) => Number(v.toFixed(2))
  const getWedgePath = (index: number, r1: number, r2: number) => {
    const cx = 0
    const cy = 250
    const startAngle = -90 + index * 60
    const endAngle = -90 + (index + 1) * 60
    const radStart = (startAngle * Math.PI) / 180
    const radEnd = (endAngle * Math.PI) / 180
    
    const x1_in = rd(cx + r1 * Math.cos(radStart))
    const y1_in = rd(cy + r1 * Math.sin(radStart))
    const x1_out = rd(cx + r2 * Math.cos(radStart))
    const y1_out = rd(cy + r2 * Math.sin(radStart))
    
    const x2_in = rd(cx + r1 * Math.cos(radEnd))
    const y2_in = rd(cy + r1 * Math.sin(radEnd))
    const x2_out = rd(cx + r2 * Math.cos(radEnd))
    const y2_out = rd(cy + r2 * Math.sin(radEnd))
    
    return `M ${x1_in} ${y1_in} L ${x1_out} ${y1_out} A ${r2} ${r2} 0 0 1 ${x2_out} ${y2_out} L ${x2_in} ${y2_in} A ${r1} ${r1} 0 0 0 ${x1_in} ${y1_in} Z`
  }

  return (
    <section id="hero" className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-4 pt-36 pb-24">
      {/* Background gradients */}
      <div 
        className="absolute inset-0 animate-gradient"
        style={{
          background: "linear-gradient(135deg, #0b0b18 0%, #1a0a2e 25%, #0b1528 50%, #1a0a2e 75%, #0b0b18 100%)",
        }}
      />
      
      {/* Grid pattern overlay */}
      <div 
        className="absolute inset-0 opacity-15"
        style={{
          backgroundImage: `linear-gradient(rgba(124,58,237,0.08) 1px, transparent 1.5px),
                           linear-gradient(90deg, rgba(124,58,237,0.08) 1px, transparent 1.5px)`,
          backgroundSize: "60px 60px",
        }}
      />

      <ParticleField />
      <FloatingOrbs />
      <InteractiveGlow />

      <div className="relative z-10 max-w-7xl mx-auto w-full px-4 md:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-4 items-center">
          
          {/* LEFT COLUMN */}
          <div className="lg:col-span-7 text-left flex flex-col items-start justify-center">
            
            {/* Version Badge */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="mb-8"
            >
              <span className="inline-flex items-center gap-2 px-5 py-2 rounded-full glass-card text-xs font-semibold uppercase tracking-wider text-purple-300 border-purple-500/25 hover:border-purple-400/40 transition-colors cursor-default">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <span>Version 1.5.1 — Now Available</span>
                <ArrowRight className="w-3.5 h-3.5 text-purple-400" />
              </span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
              className="text-5xl md:text-6xl lg:text-7xl font-extrabold mb-8 leading-[1.1] tracking-tight text-white"
            >
              Control Your PC
              <br />
              <span className="relative inline-block">
                <span className="bg-gradient-to-r from-purple-400 via-violet-300 to-purple-500 bg-clip-text text-transparent">
                  in One Swipe
                </span>
                <motion.span
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-purple-500/0 via-purple-500/50 to-purple-500/0 blur-sm"
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: 1, delay: 0.5 }}
                />
              </span>
            </motion.h1>

            {/* Subtext */}
            <motion.p
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="text-lg md:text-xl text-purple-200/70 max-w-2xl mb-12 text-pretty leading-relaxed font-light"
            >
              OrbitSwipe is a highly optimized standalone radial launcher for Windows that coordinates 
              your apps, folders, dynamic system configurations, and active stats into one gorgeous, 
              customizable glassmorphic interface.
            </motion.p>

            {/* CTA action buttons */}
            <motion.div
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-5 items-stretch sm:items-center w-full sm:w-auto"
            >
              <Button 
                size="lg" 
                className="relative group h-16 sm:h-20 px-8 text-lg sm:text-xl font-bold bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500 border-0 transition-all duration-300 overflow-hidden shadow-[0_0_30px_rgba(124,58,237,0.3)] hover:shadow-[0_0_35px_rgba(124,58,237,0.45)] rounded-2xl"
                asChild
              >
                <a href="/OrbitSwipe.exe" download className="flex items-center justify-center w-full h-full gap-2">
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full"
                    animate={{ translateX: ["100%", "-100%"] }}
                    transition={{ duration: 3.5, repeat: Infinity, repeatDelay: 2 }}
                  />
                  <Download className="w-6 h-6 relative z-10 shrink-0" />
                  <span className="relative z-10">Download Standalone</span>
                </a>
              </Button>
              
              <Button 
                size="lg" 
                variant="outline"
                className="h-12 sm:h-14 px-8 text-base sm:text-lg font-semibold glass-card border-purple-500/25 hover:border-purple-400/40 hover:bg-purple-500/10 text-white transition-all duration-300 rounded-2xl cursor-pointer flex items-center justify-center gap-2"
                onClick={() => {
                  setIsExpanded(true);
                  containerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
                }}
              >
                <Play className="w-5 h-5 shrink-0" />
                Try Live Simulator
              </Button>
            </motion.div>
          </div>

          {/* RIGHT COLUMN: Absolutely Identical Interactive Radial UI Simulator Box */}
          <div className="lg:col-span-5 w-full flex flex-col justify-center items-center lg:items-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="w-full max-w-[390px] relative group"
            >
              {/* Neon background blur */}
              <div className="absolute -inset-1 bg-gradient-to-r from-purple-500 to-violet-600 rounded-[28px] blur-xl opacity-30 group-hover:opacity-45 transition duration-1000 group-hover:duration-300" />
              
              {/* Premium PC desktop card layout wrapper */}
              <div 
                ref={containerRef}
                className="relative rounded-[28px] p-1 bg-slate-950/70 border border-white/10 backdrop-blur-2xl shadow-2xl overflow-hidden w-full h-[500px] select-none cursor-ns-resize"
                style={{
                  background: "linear-gradient(135deg, #050511 0%, #0d0a21 50%, #050512 100%)",
                }}
              >
                {/* Background accents based on active theme */}
                <div className="absolute inset-0 pointer-events-none">
                  <div 
                    className="absolute top-1/4 right-1/4 w-64 h-64 rounded-full opacity-20 blur-3xl"
                    style={{ background: preset.accent }}
                  />
                </div>

                {/* Micro simulated taskbar top header */}
                <div className="absolute top-2 left-0 right-0 px-4 flex items-center justify-between pointer-events-none z-20 text-[9px] uppercase tracking-wider font-extrabold text-purple-300/40">
                  <span>Swipe Hub Preview</span>
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500/40" />
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-500/40" />
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500/40" />
                  </div>
                </div>

                {/* Floating Ultra-Sleek Glass Theme Swatch Selector */}
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex flex-col gap-2.5 z-30 bg-slate-950/50 p-2 rounded-full border border-white/10 backdrop-blur-xl shadow-xl">
                  {glassPresets.map((p, idx) => (
                    <button
                      key={p.name}
                      onClick={() => setSelectedPreset(idx)}
                      className={`w-3.5 h-3.5 rounded-full transition-all duration-200 cursor-pointer ${
                        selectedPreset === idx ? "ring-2 ring-white scale-120" : "opacity-60 hover:opacity-100 hover:scale-110"
                      }`}
                      style={{
                        background: `linear-gradient(135deg, ${p.accent}, ${p.bg})`,
                        border: `1px solid ${p.border}`,
                      }}
                      title={p.name}
                    />
                  ))}
                </div>

                {/* Collapsed side swipe edge trigger */}
                <AnimatePresence>
                  {!isExpanded && (
                    <motion.div
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      exit={{ x: -20, opacity: 0 }}
                      className="absolute left-0 top-1/2 -translate-y-1/2 z-30 cursor-pointer"
                      onClick={() => setIsExpanded(true)}
                    >
                      <div 
                        className="w-2.5 h-20 rounded-r-lg"
                        style={{
                          background: `linear-gradient(180deg, ${preset.accent}, ${preset.accent}60)`,
                          boxShadow: `0 0 15px ${preset.accent}40`,
                        }}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Active Launcher radial dial - Centered perfectly at cy = 250, r = 180 */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ x: -300, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      exit={{ x: -300, opacity: 0 }}
                      transition={{ type: "spring", damping: 25, stiffness: 200 }}
                      className="absolute left-0 top-1/2 -translate-y-1/2"
                      style={{ width: "380px", height: "500px" }}
                    >
                      <svg 
                        viewBox="0 0 380 500" 
                        className="absolute inset-0 w-full h-full"
                        style={{ filter: `drop-shadow(0 0 30px ${preset.accent}40)` }}
                      >
                        <defs>
                          <clipPath id="heroHalfClip">
                            <rect x="0" y="0" width="250" height="500" />
                          </clipPath>
                          <radialGradient id={`heroBgGrad-${selectedPreset}`} cx="0%" cy="50%" r="100%">
                            <stop offset="0%" stopColor={preset.accent} stopOpacity="0.4" />
                            <stop offset="60%" stopColor={preset.accent} stopOpacity="0.2" />
                            <stop offset="100%" stopColor={preset.accent} stopOpacity="0.05" />
                          </radialGradient>
                        </defs>

                        {/* Radial Glass Backdrop */}
                        <circle
                          cx="0"
                          cy="250"
                          r="180"
                          fill={preset.bg}
                          stroke="none"
                          clipPath="url(#heroHalfClip)"
                          style={{ filter: "blur(0.5px)" }}
                        />
                        <circle
                          cx="0"
                          cy="250"
                          r="180"
                          fill={`url(#heroBgGrad-${selectedPreset})`}
                          clipPath="url(#heroHalfClip)"
                        />

                        {/* Ring Paths */}
                        <circle
                          cx="0"
                          cy="250"
                          r="120"
                          fill="none"
                          stroke={preset.accent}
                          strokeWidth="1.5"
                          opacity="0.35"
                          clipPath="url(#heroHalfClip)"
                        />
                        <circle
                          cx="0"
                          cy="250"
                          r="180"
                          fill="none"
                          stroke={preset.accent}
                          strokeWidth="1.8"
                          opacity="0.5"
                          clipPath="url(#heroHalfClip)"
                        />

                        {/* Stats Dashboard Hub */}
                        <circle
                          cx="0"
                          cy="250"
                          r="50"
                          fill="rgba(6, 4, 20, 0.85)"
                          stroke={preset.border}
                          strokeWidth="1.5"
                          clipPath="url(#heroHalfClip)"
                        />

                        {/* Radial Connection Lines */}
                        {[-70, -45, -20, 0, 20, 45, 70].map((angle, i) => {
                          const rad = (angle * Math.PI) / 180
                          return (
                            <line
                              key={i}
                              x1={rd(Math.cos(rad) * 50)}
                              y1={rd(250 + Math.sin(rad) * 50)}
                              x2={rd(Math.cos(rad) * 180)}
                              y2={rd(250 + Math.sin(rad) * 180)}
                              stroke={preset.border}
                              strokeWidth="0.5"
                              opacity="0.12"
                            />
                          )
                        })}

                        {/* Wedge Presets selector tabs (ICON-ONLY) */}
                        {TABS.map((tab, idx) => {
                          const isActive = idx === activeTab
                          const baseAngle = -60 + idx * 60
                          const rad = (baseAngle * Math.PI) / 180
                          const tx = Number((Math.cos(rad) * 65).toFixed(2))
                          const ty = Number((250 + Math.sin(rad) * 65).toFixed(2))

                          return (
                            <g 
                              key={tab} 
                              className="group cursor-pointer select-none"
                              onClick={() => setActiveTab(idx)}
                            >
                              <path
                                d={getWedgePath(idx, 50, 80)}
                                fill={isActive ? `${preset.accent}35` : "rgba(6, 4, 20, 0.4)"}
                                stroke={preset.border}
                                strokeWidth="1.2"
                                className="transition-all duration-300 group-hover:fill-purple-500/20"
                              />
                              <text
                                x={tx}
                                y={ty}
                                fill={isActive ? "#ffffff" : "rgba(255, 255, 255, 0.5)"}
                                fontSize={isActive ? "9" : "8"}
                                fontWeight={isActive ? "600" : "400"}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                transform={`rotate(${baseAngle + 90}, ${tx}, ${ty})`}
                                className="transition-all duration-200"
                                style={{
                                  filter: isActive ? `drop-shadow(0 0 5px ${preset.accent})` : "none",
                                }}
                              >
                                {tab}
                              </text>
                            </g>
                          )
                        })}
                      </svg>

                      {/* Clickable Dashboard / Media Player inside hub */}
                      <div 
                        className="absolute flex flex-col items-center justify-center text-white text-center select-none cursor-pointer hover:bg-white/5 rounded-full p-1 transition-all duration-300"
                        style={{
                          left: "0px",
                          top: "50%",
                          transform: "translateY(-50%)",
                          width: "48px",
                          height: "85px",
                        }}
                        onClick={() => setHubMode(prev => prev === "stats" ? "media" : "stats")}
                        title="Click to toggle between System Stats and Media Player!"
                      >
                        {hubMode === "stats" ? (
                          <div className="flex flex-col items-center justify-center w-full">
                            <div className="text-[7.5px] text-green-400 font-bold flex items-center gap-0.5">
                              <span>⚡</span>
                              <span>100%</span>
                            </div>
                            <div className="text-[6.5px] text-white/55 font-bold uppercase tracking-wider mt-0.5">
                              MONDAY
                            </div>
                            <div className="text-xs font-extrabold leading-none text-white my-1 select-none">
                              {time.hour}:{time.minute}
                            </div>
                            <div className="w-8 h-[0.5px] bg-white/20 my-0.5" />
                            <div className="text-[6.5px] text-white/80 font-medium space-y-0.5">
                              <div>CPU 32%</div>
                              <div>RAM 90%</div>
                            </div>
                            <div className="w-8 h-[0.5px] bg-white/20 my-0.5" />
                            <div className="text-[6.5px] text-sky-400 font-semibold flex items-center gap-0.5">
                              <span>📶</span>
                              <span>6 KB/s</span>
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col items-center justify-center w-full px-0.5" onClick={(e) => e.stopPropagation()}>
                            <div className="w-4 h-4 rounded-full border border-purple-400/50 flex items-center justify-center bg-black/40 mb-1">
                              <span className="text-[9px]">🔵</span>
                            </div>
                            <div className="text-[6.5px] font-extrabold text-white w-10 truncate text-center select-none mb-0.5">
                              Google Search
                            </div>
                            <div className="w-8 h-[2px] bg-white/20 rounded-full my-1 relative">
                              <div 
                                className="absolute left-0 top-0 h-full w-[60%]"
                                style={{ backgroundColor: preset.accent }}
                              />
                            </div>
                            <div className="text-[4.5px] text-white/40 tracking-wider mb-0.5">58:07</div>
                            <div className="flex items-center justify-center gap-1 my-0.5 text-[7px] text-white/80">
                              <span>⏮</span>
                              <span>⏸</span>
                              <span>⏭</span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Inner Ring Icons (Perfectly aligned HTML layers for maximum smoothness!) */}
                      <AnimatePresence>
                        {innerItems.map((item, i) => {
                          const innerStep = 360 / innerItems.length
                          let a_norm = (i * innerStep + rotation + 180) % 360 - 180
                          const d = Math.abs(a_norm)
                          let opacity = 1
                          if (d < 78) opacity = 1
                          else if (d > 102) opacity = 0
                          else opacity = (102 - d) / 24.0

                          if (opacity <= 0) return null

                          const rad = (a_norm * Math.PI) / 180
                          const radius = 120
                          const x = Math.cos(rad) * radius
                          const y = 250 + Math.sin(rad) * radius
                          const isHovered = hoveredItem === `inner-${i}`

                          return (
                            <motion.div
                              key={`${activeTab}-inner-${i}`}
                              className="absolute flex flex-col items-center cursor-pointer"
                              style={{ left: 0, top: 0, opacity }}
                              onMouseEnter={() => setHoveredItem(`inner-${i}`)}
                              onMouseLeave={() => setHoveredItem(null)}
                              whileHover={{ scale: 1.15 }}
                              initial={{ opacity: 0, scale: 0 }}
                              animate={{ 
                                opacity, 
                                scale: 1, 
                                x: x - 16, 
                                y: y - 16 
                              }}
                              exit={{ opacity: 0, scale: 0 }}
                              transition={{ type: "spring", damping: 20, stiffness: 150 }}
                            >
                              <div
                                className="w-8 h-8 rounded-full flex items-center justify-center text-base transition-all duration-200"
                                style={{
                                  background: isHovered 
                                    ? `linear-gradient(135deg, ${preset.accent}80, ${preset.accent}40)`
                                    : preset.bg,
                                  border: `1.5px solid ${isHovered ? preset.border : preset.accent + "50"}`,
                                  boxShadow: isHovered ? `0 0 12px ${preset.accent}50` : `0 2px 6px rgba(0,0,0,0.3)`,
                                }}
                              >
                                {item.emoji}
                              </div>
                              <span 
                                className="text-[6px] mt-0.5 whitespace-nowrap font-medium pointer-events-none select-none"
                                style={{ color: isHovered ? preset.accent : "rgba(255,255,255,0.6)" }}
                              >
                                {item.label}
                              </span>
                            </motion.div>
                          )
                        })}
                      </AnimatePresence>

                      {/* Outer Ring Icons */}
                      <AnimatePresence>
                        {outerItems.map((item, i) => {
                          const outerStep = 360 / outerItems.length
                          let a_norm = (i * outerStep + rotation + 180) % 360 - 180
                          const d = Math.abs(a_norm)
                          let opacity = 1
                          if (d < 78) opacity = 1
                          else if (d > 102) opacity = 0
                          else opacity = (102 - d) / 24.0

                          if (opacity <= 0) return null

                          const rad = (a_norm * Math.PI) / 180
                          const radius = 180
                          const x = Math.cos(rad) * radius
                          const y = 250 + Math.sin(rad) * radius
                          const isHovered = hoveredItem === `outer-${i}`

                          return (
                            <motion.div
                              key={`${activeTab}-outer-${i}`}
                              className="absolute flex flex-col items-center cursor-pointer"
                              style={{ left: 0, top: 0, opacity }}
                              onMouseEnter={() => setHoveredItem(`outer-${i}`)}
                              onMouseLeave={() => setHoveredItem(null)}
                              whileHover={{ scale: 1.15 }}
                              initial={{ opacity: 0, scale: 0 }}
                              animate={{ 
                                opacity, 
                                scale: 1, 
                                x: x - 20, 
                                y: y - 20 
                              }}
                              exit={{ opacity: 0, scale: 0 }}
                              transition={{ type: "spring", damping: 20, stiffness: 150 }}
                            >
                              <div
                                className="w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all duration-200"
                                style={{
                                  background: isHovered 
                                    ? `linear-gradient(135deg, ${preset.accent}80, ${preset.accent}40)`
                                    : preset.bg,
                                  border: `2px solid ${isHovered ? preset.border : preset.accent + "60"}`,
                                  boxShadow: isHovered ? `0 0 16px ${preset.accent}60` : `0 3px 10px rgba(0,0,0,0.3)`,
                                }}
                              >
                                {item.emoji}
                              </div>
                              <span 
                                className="text-[7px] mt-0.5 whitespace-nowrap font-medium pointer-events-none select-none"
                                style={{ color: isHovered ? preset.accent : "rgba(255,255,255,0.6)" }}
                              >
                                {item.label}
                              </span>
                            </motion.div>
                          )
                        })}
                      </AnimatePresence>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Unified bottom row layout containing Collapse, Quick Actions, and Scroll Tip */}
                <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-3 bg-slate-950/65 px-3.5 py-1.5 rounded-full border border-white/10 backdrop-blur-md shadow-lg z-20 whitespace-nowrap">
                  {/* Left Side: Collapse/Expand */}
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="px-2.5 py-0.5 rounded-md text-[8.5px] font-bold bg-white/10 hover:bg-white/20 text-white/80 transition-colors cursor-pointer border-r border-white/15 pr-3 mr-0.5"
                  >
                    {isExpanded ? "Collapse" : "Expand"}
                  </button>

                  {/* The 4 Quick Actions (Recents, Favorites, Toolbox, Switch Mode) */}
                  <div className="flex items-center gap-2 border-r border-white/15 pr-2.5">
                    <button
                      onClick={() => { setActiveTab(0); setIsExpanded(true); }}
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs transition-all duration-150 cursor-pointer ${
                        activeTab === 0 && isExpanded ? "bg-white/25 text-white scale-110" : "text-white/60 hover:text-white hover:bg-white/10"
                      }`}
                      title="Recents Menu"
                    >
                      🕒
                    </button>
                    <button
                      onClick={() => { setActiveTab(1); setIsExpanded(true); }}
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs transition-all duration-150 cursor-pointer ${
                        activeTab === 1 && isExpanded ? "bg-white/25 text-white scale-110" : "text-white/60 hover:text-white hover:bg-white/10"
                      }`}
                      title="Favorites Menu"
                    >
                      ⭐
                    </button>
                    <button
                      onClick={() => { setActiveTab(2); setIsExpanded(true); }}
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs transition-all duration-150 cursor-pointer ${
                        activeTab === 2 && isExpanded ? "bg-white/25 text-white scale-110" : "text-white/60 hover:text-white hover:bg-white/10"
                      }`}
                      title="Toolbox Menu"
                    >
                      ⚙️
                    </button>
                    <button
                      onClick={() => { setHubMode(prev => prev === "stats" ? "media" : "stats"); setIsExpanded(true); }}
                      className="w-6 h-6 rounded-full flex items-center justify-center text-xs text-white/60 hover:text-white hover:bg-white/10 transition-all duration-150 cursor-pointer"
                      title="Toggle Hub Mode (Stats/Media)"
                    >
                      🔄
                    </button>
                  </div>

                  {/* Scroll workspace action tip */}
                  <div className="text-[7.5px] font-bold text-white/40 flex items-center gap-1 select-none">
                    <span>🖱️</span>
                    <span>Scroll/Drag to rotate</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

        </div>

        {/* BOTTOM SECTION: Majestic Floating Glass Widescreen Stats Telemetry Bar */}
        <motion.div
          initial={{ opacity: 0, y: 35 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-16 mx-auto max-w-5xl w-full px-12 py-8 rounded-3xl glass-card border border-purple-500/25 shadow-2xl backdrop-blur-2xl flex flex-wrap justify-around items-center gap-8 md:gap-12"
        >
          {[
            { label: "Launcher", value: "Radial", suffix: "" },
            { label: "System Tools", value: "90+", suffix: "" },
            { label: "Offline & Fast", value: "100", suffix: "%" },
            { label: "Groups", value: "Workspace", suffix: "" },
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.7 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.5 + index * 0.1 }}
              className="text-center group cursor-default"
            >
              <div className="text-3xl md:text-4xl font-extrabold tracking-tight">
                <span className="bg-gradient-to-r from-purple-300 to-violet-300 bg-clip-text text-transparent group-hover:from-purple-200 group-hover:to-violet-200 transition-all">
                  {stat.value}
                </span>
                <span className="text-purple-400/60 font-bold ml-0.5">{stat.suffix}</span>
              </div>
              <div className="text-xs font-bold uppercase tracking-wider text-purple-200/50 mt-1.5">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5, duration: 1 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.a
          href="#features"
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          className="flex flex-col items-center gap-1.5 text-muted-foreground hover:text-purple-400 transition-colors"
        >
          <span className="text-[10px] uppercase tracking-widest font-semibold">Scroll to explore</span>
          <ChevronDown className="w-4 h-4" />
        </motion.a>
      </motion.div>
    </section>
  )
}
