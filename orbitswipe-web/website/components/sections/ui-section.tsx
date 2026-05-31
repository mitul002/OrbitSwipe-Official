"use client"

import { motion, AnimatePresence } from "framer-motion"
import { useState, useEffect, useRef } from "react"

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

// Expanded lists to ensure absolute abundance of apps, completely packing the rings
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

export function UISection() {
  const [selectedPreset, setSelectedPreset] = useState(0)
  const [isExpanded, setIsExpanded] = useState(true)
  const [rotation, setRotation] = useState(0)
  const [hoveredItem, setHoveredItem] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState(1) // Defaults to Favorites tab
  const [time, setTime] = useState({ hour: "10", minute: "43", period: "PM" })
  const [stats, setStats] = useState({ ram: 90, cpu: 32, battery: 100, network: "6 KB/s" })
  const [hubMode, setHubMode] = useState<"stats" | "media">("stats")
  const [isPlaying, setIsPlaying] = useState(true)
  
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
      setStats(prev => ({
        ...prev,
        ram: 90,
        cpu: 32,
        network: "6 KB/s"
      }))
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // Scroll and touch drag interceptor to rotate app icons on desktop and mobile
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleWheelPrevent = (e: WheelEvent) => {
      e.preventDefault() // Completely stops the web page from scrolling
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
        e.preventDefault() // Prevent standard page scroll when dragging active dial
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

  // Helper to get active tab items
  const getTabItems = () => {
    switch (activeTab) {
      case 0: return RECENTS_ITEMS
      case 1: return FAVORITES_ITEMS
      case 2: return TOOLBOX_ITEMS
      default: return FAVORITES_ITEMS
    }
  }

  const tabItems = getTabItems()
  
  // Distribute based on tab config
  const innerLimit = 18
  const innerItems = tabItems.slice(0, innerLimit)
  const outerItems = tabItems.slice(innerLimit)

  // Generate SVG path for wedges (sector of radius r1 to r2) flat at cx = 0
  // All coordinates rounded to 2dp to prevent SSR/CSR hydration mismatch
  const r = (v: number) => Number(v.toFixed(2))
  const getWedgePath = (index: number, r1: number, r2: number) => {
    const cx = 0
    const cy = 250
    const startAngle = -90 + index * 60
    const endAngle = -90 + (index + 1) * 60
    const radStart = (startAngle * Math.PI) / 180
    const radEnd = (endAngle * Math.PI) / 180
    
    const x1_in = r(cx + r1 * Math.cos(radStart))
    const y1_in = r(cy + r1 * Math.sin(radStart))
    const x1_out = r(cx + r2 * Math.cos(radStart))
    const y1_out = r(cy + r2 * Math.sin(radStart))
    
    const x2_in = r(cx + r1 * Math.cos(radEnd))
    const y2_in = r(cy + r1 * Math.sin(radEnd))
    const x2_out = r(cx + r2 * Math.cos(radEnd))
    const y2_out = r(cy + r2 * Math.sin(radEnd))
    
    return `M ${x1_in} ${y1_in} L ${x1_out} ${y1_out} A ${r2} ${r2} 0 0 1 ${x2_out} ${y2_out} L ${x2_in} ${y2_in} A ${r1} ${r1} 0 0 0 ${x1_in} ${y1_in} Z`
  }

  return (
    <section id="ui" className="relative py-24 px-4 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-purple-950/5 to-background" />

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium mb-4">
            Visual Experience
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-white via-purple-200 to-white bg-clip-text text-transparent">
              Glass Radial Interface
            </span>
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Flat-anchored 180° radial launcher featuring scrolling wheel, dashboard, and media center
          </p>
        </motion.div>

        {/* Main visualization */}
        <div className="relative max-w-5xl mx-auto">
          {/* Desktop frame */}
          <div 
            ref={containerRef}
            className="relative rounded-2xl overflow-hidden border border-white/10 select-none cursor-ns-resize"
            style={{
              background: "linear-gradient(135deg, #05050f 0%, #0c0c1f 50%, #050510 100%)",
              aspectRatio: "16/10",
              minHeight: "500px",
            }}
          >
            {/* Background accents */}
            <div className="absolute inset-0 pointer-events-none">
              <div 
                className="absolute top-1/4 right-1/4 w-64 h-64 rounded-full opacity-20 blur-3xl"
                style={{ background: preset.accent }}
              />
            </div>

            {/* Collapsed trigger */}
            <AnimatePresence>
              {!isExpanded && (
                <motion.div
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  exit={{ x: -20, opacity: 0 }}
                  className="absolute left-0 top-1/2 -translate-y-1/2 z-20 cursor-pointer"
                  onClick={() => setIsExpanded(true)}
                >
                  <div 
                    className="w-3 h-24 rounded-r-xl"
                    style={{
                      background: `linear-gradient(180deg, ${preset.accent}, ${preset.accent}60)`,
                      boxShadow: `0 0 25px ${preset.accent}50`,
                    }}
                  >
                    <motion.div 
                      className="absolute left-1 top-1/2 -translate-y-1/2 w-1 h-10 rounded-full bg-white/40"
                      animate={{ opacity: [0.4, 0.8, 0.4] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Main OrbitSwipe launcher */}
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
                  {/* SVG for the half-circle structure - cx centered mathematically at exactly 0 */}
                  <svg 
                    viewBox="0 0 380 500" 
                    className="absolute inset-0 w-full h-full"
                    style={{ filter: `drop-shadow(0 0 30px ${preset.accent}40)` }}
                  >
                    <defs>
                      <clipPath id="halfCircleClip">
                        <rect x="0" y="0" width="250" height="500" />
                      </clipPath>
                      <radialGradient id={`bgGrad-${selectedPreset}`} cx="0%" cy="50%" r="100%">
                        <stop offset="0%" stopColor={preset.accent} stopOpacity="0.4" />
                        <stop offset="60%" stopColor={preset.accent} stopOpacity="0.2" />
                        <stop offset="100%" stopColor={preset.accent} stopOpacity="0.05" />
                      </radialGradient>
                    </defs>

                    {/* Main half-circle background centered at cx = 0, exactly aligned with Ro = 180 (No 3rd ring border) */}
                    <circle
                      cx="0"
                      cy="250"
                      r="180"
                      fill={preset.bg}
                      stroke="none"
                      clipPath="url(#halfCircleClip)"
                      style={{ filter: "blur(0.5px)" }}
                    />
                    
                    {/* Gradient overlay */}
                    <circle
                      cx="0"
                      cy="250"
                      r="180"
                      fill={`url(#bgGrad-${selectedPreset})`}
                      clipPath="url(#halfCircleClip)"
                    />

                    {/* Solid Inner Ring Path (Ri = 120px) */}
                    <circle
                      cx="0"
                      cy="250"
                      r="120"
                      fill="none"
                      stroke={preset.accent}
                      strokeWidth="1.5"
                      opacity="0.35"
                      clipPath="url(#halfCircleClip)"
                    />

                    {/* Solid Outer Ring Path (Ro = 180px) */}
                    <circle
                      cx="0"
                      cy="250"
                      r="180"
                      fill="none"
                      stroke={preset.accent}
                      strokeWidth="1.8"
                      opacity="0.5"
                      clipPath="url(#halfCircleClip)"
                    />

                    {/* Hub circle (dashboard area) */}
                    <circle
                      cx="0"
                      cy="250"
                      r="50"
                      fill="rgba(6, 4, 20, 0.85)"
                      stroke={preset.border}
                      strokeWidth="1.5"
                      clipPath="url(#halfCircleClip)"
                    />

                    {/* Radial connection lines */}
                    {[-70, -45, -20, 0, 20, 45, 70].map((angle, i) => {
                      const rad = (angle * Math.PI) / 180
                      return (
                        <line
                          key={i}
                          x1={r(Math.cos(rad) * 50)}
                          y1={r(250 + Math.sin(rad) * 50)}
                          x2={r(Math.cos(rad) * 180)}
                          y2={r(250 + Math.sin(rad) * 180)}
                          stroke={preset.border}
                          strokeWidth="0.5"
                          opacity="0.12"
                        />
                      )
                    })}

                    {/* 3 Wedges Selector Ring (Radius 50px to 80px) */}
                    {TABS.map((tab, i) => {
                      const isActive = i === activeTab
                      const baseAngle = -60 + (i * 60)
                      const rad = (baseAngle * Math.PI) / 180
                      const tx = r(Math.cos(rad) * 65)
                      const ty = r(250 + Math.sin(rad) * 65)

                      return (
                        <g 
                          key={tab} 
                          className="group cursor-pointer select-none" 
                          onClick={() => setActiveTab(i)}
                        >
                          <path
                            d={getWedgePath(i, 50, 80)}
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
                    className="absolute flex flex-col items-center justify-center text-white text-center select-none cursor-pointer hover:bg-white/5 rounded-full p-1 transition-all duration-300 animate-fade-in"
                    style={{
                      left: "0px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      width: "48px",
                      height: "85px",
                    }}
                    onClick={() => setHubMode(prev => prev === "stats" ? "media" : "stats")}
                    title="Click here to toggle between System Stats and Media Player!"
                  >
                    {hubMode === "stats" ? (
                      // 📊 System Stats View (2nd Image) - Exactly matching desktop layout!
                      <div className="flex flex-col items-center justify-center w-full">
                        {/* Battery Icon & Percentage */}
                        <div className="text-[7.5px] text-green-400 font-bold flex items-center gap-0.5">
                          <span>⚡</span>
                          <span>{stats.battery}%</span>
                        </div>
                        
                        {/* Day (MONDAY) */}
                        <div className="text-[6.5px] text-white/55 font-bold uppercase tracking-wider mt-0.5">
                          MONDAY
                        </div>

                        {/* Big Digital Clock */}
                        <div className="text-xs font-extrabold leading-none text-white my-1 select-none">
                          {time.hour}:{time.minute}
                        </div>

                        {/* Separator */}
                        <div className="w-8 h-[0.5px] bg-white/20 my-0.5" />

                        {/* CPU & RAM stats */}
                        <div className="text-[6.5px] text-white/80 font-medium space-y-0.5">
                          <div>CPU {stats.cpu}%</div>
                          <div>RAM {stats.ram}%</div>
                        </div>

                        {/* Separator */}
                        <div className="w-8 h-[0.5px] bg-white/20 my-0.5" />

                        {/* Network Speed */}
                        <div className="text-[6.5px] text-sky-400 font-semibold flex items-center gap-0.5">
                          <span>📶</span>
                          <span>{stats.network}</span>
                        </div>
                      </div>
                    ) : (
                      // 🎵 Active Media Player View (3rd Image) - Fully matching styling!
                      <div className="flex flex-col items-center justify-center w-full px-0.5" onClick={(e) => e.stopPropagation()}>
                        {/* Chrome Icon centered at top with circular frame border */}
                        <div className="w-4 h-4 rounded-full border border-purple-400/50 flex items-center justify-center bg-black/40 mb-1">
                          <span className="text-[9px]">🔵</span>
                        </div>
                        
                        {/* Track title ("Google Search") */}
                        <div 
                          className="text-[6.5px] font-extrabold text-white w-10 truncate text-center select-none mb-0.5 cursor-help"
                          title="Google Search"
                          onClick={() => setHubMode("stats")}
                        >
                          Google Search
                        </div>

                        {/* Seeker Slider (Progress seeker bar with circle thumb) */}
                        <div className="w-8 h-[2px] bg-white/20 rounded-full my-1 relative cursor-pointer group">
                          <motion.div 
                            className="absolute left-0 top-0 h-full"
                            style={{ backgroundColor: preset.accent }}
                            animate={isPlaying ? { width: ["20%", "90%", "20%"] } : {}}
                            transition={{ duration: 10, ease: "linear", repeat: Infinity }}
                          />
                          {/* Circular slider thumb/knob */}
                          <motion.div 
                            className="absolute w-1 h-1 rounded-full bg-white -top-[1px] shadow-sm shadow-black"
                            animate={isPlaying ? { left: ["20%", "90%", "20%"] } : {}}
                            transition={{ duration: 10, ease: "linear", repeat: Infinity }}
                            style={{ marginLeft: "-2px" }}
                          />
                        </div>
                        
                        {/* Timestamp underneath seeker */}
                        <div className="text-[4.5px] text-white/40 tracking-wider mb-0.5">58:07</div>

                        {/* Playback Controls (Middle Play/Pause is larger) */}
                        <div className="flex items-center justify-center gap-1.5 my-0.5">
                          <button 
                            onClick={(e) => { e.stopPropagation(); }}
                            className="text-[6px] hover:text-purple-400 transition-colors text-white/70 active:scale-95"
                          >
                            ⏮
                          </button>
                          <button 
                            onClick={(e) => { e.stopPropagation(); setIsPlaying(!isPlaying); }}
                            className="text-[8px] hover:text-purple-400 transition-colors text-white font-black active:scale-95 bg-white/10 p-0.5 rounded-full"
                          >
                            {isPlaying ? "⏸" : "▶️"}
                          </button>
                          <button 
                            onClick={(e) => { e.stopPropagation(); }}
                            className="text-[6px] hover:text-purple-400 transition-colors text-white/70 active:scale-95"
                          >
                            ⏭
                          </button>
                        </div>

                        {/* Animated Visualizer spectrum bars at bottom */}
                        <div className="flex items-end gap-[1px] h-2.5 mt-0.5 overflow-hidden w-9 justify-center">
                          {[...Array(6)].map((_, idx) => (
                            <motion.div
                              key={idx}
                              className="w-[1.5px] rounded-t"
                              style={{ backgroundColor: preset.accent }}
                              animate={isPlaying ? {
                                height: [
                                  "1px", 
                                  `${Math.floor(Math.random() * 8) + 2}px`, 
                                  "1px"
                                ]
                              } : { height: "1.5px" }}
                              transition={{
                                duration: 0.35 + idx * 0.08,
                                repeat: Infinity,
                                ease: "easeInOut"
                              }}
                              style={{ height: "1.5px" }}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Inner Ring Icons (Distributed perfectly and evenly around the entire 360° to eliminate gaps!) */}
                  <AnimatePresence>
                    {innerItems.map((item, i) => {
                      // Calculate step dynamically for perfect distribution
                      const innerStep = 360 / innerItems.length
                      
                      // Normalize angle between [-180, 180]
                      let a_norm = (i * innerStep + rotation + 180) % 360 - 180
                      const d = Math.abs(a_norm)
                      
                      // Opacity fading logic mapped directly from python source!
                      let opacity = 1
                      if (d < 78) opacity = 1
                      else if (d > 102) opacity = 0
                      else opacity = (102 - d) / 24.0

                      // Optimizing RAM footprint & visual overlay by dropping off-screen nodes completely
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

                  {/* Outer Ring Icons (Distributed perfectly and evenly around the entire 360° to eliminate gaps!) */}
                  <AnimatePresence>
                    {outerItems.map((item, i) => {
                      // Calculate step dynamically for perfect distribution
                      const outerStep = 360 / outerItems.length
                      
                      // Normalize angle between [-180, 180]
                      let a_norm = (i * outerStep + rotation + 180) % 360 - 180
                      const d = Math.abs(a_norm)
                      
                      // Opacity fading logic mapped directly from python source!
                      let opacity = 1
                      if (d < 78) opacity = 1
                      else if (d > 102) opacity = 0
                      else opacity = (102 - d) / 24.0

                      // Optimizing RAM footprint & visual overlay by dropping off-screen nodes completely
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

            {/* Toggle hint */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="absolute bottom-4 left-4 px-3 py-1.5 rounded-lg text-[10px] font-medium bg-white/5 hover:bg-white/10 text-white/60 transition-colors z-20"
            >
              {isExpanded ? "Click to Collapse" : "Click to Expand"}
            </button>

            {/* Scroll Instruction Overlay */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 text-[9px] text-white/40 flex items-center gap-1 bg-black/30 px-2 py-1 rounded border border-white/5 backdrop-blur pointer-events-none select-none z-20">
              <span>🖱️</span>
              <span>Scroll mouse wheel to rotate 180° arc</span>
            </div>

            {/* Integrated Sleek Vertical Control Panel - Hidden on small screens, absolutely gorgeous on medium/large screens */}
            <div className="absolute right-4 top-1/2 -translate-y-1/2 w-[210px] bg-slate-950/60 border border-white/15 backdrop-blur-xl rounded-[20px] p-4 hidden md:flex flex-col gap-5 z-20 shadow-2xl">
              {/* Header */}
              <div className="text-[10px] font-extrabold uppercase tracking-widest text-purple-300 border-b border-white/10 pb-2 select-none">
                ⚙️ Swipe Controller
              </div>
              
              {/* Presets Grid */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-white/50">Glass Theme</span>
                <div className="grid grid-cols-5 gap-1.5">
                  {glassPresets.map((p, i) => (
                    <button
                      key={p.name}
                      onClick={() => setSelectedPreset(i)}
                      className={`w-7 h-7 rounded-lg transition-all duration-200 relative group cursor-pointer ${
                        selectedPreset === i ? "ring-2 ring-white ring-offset-1 ring-offset-background scale-110" : "opacity-60 hover:opacity-100"
                      }`}
                      style={{
                        background: `linear-gradient(135deg, ${p.accent}, ${p.bg})`,
                        border: `1.5px solid ${p.border}`,
                      }}
                      title={p.name}
                    >
                      {/* Tooltip on hover */}
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-0.5 rounded text-[8px] font-semibold bg-slate-950/90 border border-white/15 text-white opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-30 shadow-lg">
                        {p.name}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Active Tab Stack */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-white/50">Active Tab</span>
                <div className="flex flex-col gap-1.5">
                  {TABS.map((tab, i) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(i)}
                      className={`w-full py-2 rounded-xl text-[10px] font-bold tracking-wide uppercase transition-all duration-250 cursor-pointer ${
                        activeTab === i 
                          ? "text-white" 
                          : "text-white/60 hover:text-white hover:bg-white/5"
                      }`}
                      style={{
                        background: activeTab === i ? preset.accent : "rgba(255,255,255,0.03)",
                        border: activeTab === i ? `1px solid ${preset.border}` : "1px solid rgba(255,255,255,0.05)",
                        boxShadow: activeTab === i ? `0 0 15px ${preset.accent}40` : "none"
                      }}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              {/* Hub Mode Stack */}
              <div className="flex flex-col gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-white/50">Hub Dashboard</span>
                <button
                  onClick={() => setHubMode(prev => prev === "stats" ? "media" : "stats")}
                  className="w-full py-2.5 rounded-xl text-[10px] font-bold tracking-wide uppercase transition-all duration-200 text-white shadow-xl cursor-pointer"
                  style={{
                    background: preset.accent,
                    border: `1.5px solid ${preset.border}`,
                    boxShadow: `0 0 15px ${preset.accent}40`
                  }}
                >
                  {hubMode === "stats" ? "📊 System Stats" : "🎵 Media Player"}
                </button>
              </div>
            </div>
          </div>

          {/* Controls - Visible only on mobile since they are now integrated inside the frame on desktop */}
          <div className="mt-8 flex md:hidden flex-col items-center justify-center gap-6">
            {/* Glass presets */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground">Theme:</span>
              <div className="flex gap-2">
                {glassPresets.map((p, i) => (
                  <button
                    key={p.name}
                    onClick={() => setSelectedPreset(i)}
                    className={`w-8 h-8 rounded-lg transition-all duration-200 ${
                      selectedPreset === i ? "ring-2 ring-white ring-offset-2 ring-offset-background scale-110" : "opacity-60 hover:opacity-100"
                    }`}
                    style={{
                      background: `linear-gradient(135deg, ${p.accent}, ${p.bg})`,
                      border: `2px solid ${p.border}`,
                    }}
                    title={p.name}
                  />
                ))}
              </div>
            </div>

            {/* Tab selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Tab:</span>
              {TABS.map((tab, i) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(i)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                    activeTab === i 
                      ? "text-white" 
                      : "text-muted-foreground hover:text-white/80"
                  }`}
                  style={{
                    background: activeTab === i ? preset.accent : "transparent",
                  }}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Hub Mode selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Hub Mode:</span>
              <button
                onClick={() => setHubMode(prev => prev === "stats" ? "media" : "stats")}
                className="px-3 py-1 rounded-md text-xs font-medium transition-all text-white hover:opacity-90 active:scale-95"
                style={{
                  background: preset.accent,
                }}
              >
                {hubMode === "stats" ? "📊 Stats" : "🎵 Media"}
              </button>
            </div>
          </div>
        </div>

        {/* Feature highlights */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto"
        >
          {[
            { title: "Flat Half-Circle", desc: "Anchored at cx = 0 for perfect flat edge" },
            { title: "Scroll Interceptor", desc: "Prevents page scroll inside simulator" },
            { title: "Max-Abundance Icons", desc: "Deeply packed outer & inner rings" },
            { title: "High-Fidelity Stats", desc: "Live clock, battery, CPU & RAM stats" },
          ].map((feat, i) => (
            <div 
              key={i}
              className="p-4 rounded-xl text-center"
              style={{
                background: `linear-gradient(135deg, ${preset.bg}, transparent)`,
                border: `1px solid ${preset.accent}30`,
              }}
            >
              <h4 className="font-semibold text-sm text-foreground mb-1">{feat.title}</h4>
              <p className="text-xs text-muted-foreground">{feat.desc}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
