"use client"

import { motion, useMotionTemplate, useMotionValue } from "framer-motion"
import { useRef } from "react"
import { 
  Circle, 
  PinIcon, 
  Search, 
  SlidersHorizontal, 
  FolderOpen, 
  MousePointer2,
  Palette,
  Timer,
  Power,
  Droplet
} from "lucide-react"

const features = [
  {
    icon: Circle,
    title: "Radial Launcher",
    description: "Access everything instantly with a smooth, swipe-based circular menu. Opens right where your cursor is.",
    gradient: "from-purple-500 to-violet-600",
    tag: "Core",
  },
  {
    icon: PinIcon,
    title: "WinTop Manager",
    description: "Pin any window to stay always on top while you work or game. Never lose sight of important windows.",
    gradient: "from-violet-500 to-purple-600",
    tag: "Popular",
  },
  {
    icon: Search,
    title: "Smart Search",
    description: "Find apps, files, and tools instantly without opening the Start Menu. AI-powered suggestions.",
    gradient: "from-blue-500 to-purple-600",
    tag: "New",
  },
  {
    icon: SlidersHorizontal,
    title: "Hardware Control",
    description: "Adjust volume and brightness with fluid radial sliders. Visual feedback with smooth animations.",
    gradient: "from-purple-600 to-pink-500",
    tag: "Essential",
  },
  {
    icon: FolderOpen,
    title: "Workspace Groups",
    description: "Launch your entire setup (apps, tools, folders) in one click. Perfect for different projects.",
    gradient: "from-indigo-500 to-purple-600",
    tag: "Productivity",
  },
  {
    icon: MousePointer2,
    title: "Drag & Drop",
    description: "Add apps, links, and scripts effortlessly. Intuitive customization without complex settings.",
    gradient: "from-purple-500 to-blue-600",
    tag: "Easy",
  },
  {
    icon: Palette,
    title: "Custom Glass Themes",
    description: "Create or select from beautiful glass UI presets that adapt dynamically to your desktop. Fully customizable accents.",
    gradient: "from-pink-500 to-purple-600",
    tag: "Design",
  },
  {
    icon: Timer,
    title: "Auto-Hide Trigger",
    description: "Activate from screen edges with hover. Configure delay, sensitivity, and trigger zones.",
    gradient: "from-purple-600 to-violet-500",
    tag: "Smart",
  },
  {
    icon: Power,
    title: "Power Manager",
    description: "Lock, sleep, restart, hibernate, or shut down your PC with instant execution or scheduled countdown timers.",
    gradient: "from-violet-600 to-purple-500",
    tag: "Power",
  },
  {
    icon: Droplet,
    title: "Color Picker",
    description: "Built-in screen magnifier with hex/rgb copy and color history tracking.",
    gradient: "from-fuchsia-500 to-purple-600",
    tag: "Tool",
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" }
  },
}

function FeatureCard({ feature, index }: { feature: typeof features[0]; index: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    mouseX.set(e.clientX - rect.left)
    mouseY.set(e.clientY - rect.top)
  }

  return (
    <motion.div
      ref={ref}
      variants={itemVariants}
      onMouseMove={handleMouseMove}
      className="group relative"
    >
      <div className="relative h-full p-8 rounded-2xl glass-card hover:bg-white/[0.07] transition-all duration-500 overflow-hidden">
        {/* Mouse follow spotlight */}
        <motion.div
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
          style={{
            background: useMotionTemplate`radial-gradient(300px circle at ${mouseX}px ${mouseY}px, rgba(124,58,237,0.1), transparent 80%)`,
          }}
        />

        {/* Tag */}
        <div className="absolute top-4 right-4">
          <span className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded-full bg-gradient-to-r ${feature.gradient} text-white/90 font-medium`}>
            {feature.tag}
          </span>
        </div>
        
        {/* Icon */}
        <div className={`relative w-14 h-14 rounded-xl bg-gradient-to-br ${feature.gradient} p-0.5 mb-6 group-hover:scale-110 transition-transform duration-300`}>
          <div className="w-full h-full rounded-xl bg-background/80 flex items-center justify-center">
            <feature.icon className="w-6 h-6 text-purple-400" />
          </div>
        </div>

        {/* Content */}
        <h3 className="text-xl font-semibold text-foreground mb-3 group-hover:text-purple-300 transition-colors">
          {feature.title}
        </h3>
        <p className="text-muted-foreground leading-relaxed text-sm">
          {feature.description}
        </p>

        {/* Border glow on hover */}
        <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className="absolute inset-0 rounded-2xl border border-purple-500/40" />
        </div>

        {/* Corner accent */}
        <div className="absolute bottom-0 right-0 w-20 h-20 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
          <div className={`absolute inset-0 bg-gradient-to-tl ${feature.gradient} opacity-10 rounded-tl-3xl`} />
        </div>
      </div>
    </motion.div>
  )
}

export function FeaturesSection() {
  return (
    <section id="features" className="relative py-32 px-4 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-purple-950/5 to-background" />
      
      {/* Decorative elements */}
      <div className="absolute top-1/4 left-0 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[120px] -translate-x-1/2" />
      <div className="absolute bottom-1/4 right-0 w-[600px] h-[600px] bg-violet-600/10 rounded-full blur-[120px] translate-x-1/2" />

      {/* Decorative lines */}
      <div className="absolute top-0 left-1/4 w-px h-full bg-gradient-to-b from-transparent via-purple-500/10 to-transparent" />
      <div className="absolute top-0 right-1/4 w-px h-full bg-gradient-to-b from-transparent via-purple-500/10 to-transparent" />

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="text-center mb-20"
        >
          <span className="inline-block px-4 py-1.5 rounded-full glass-card text-sm text-purple-300 mb-4">
            Core Features
          </span>
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            <span className="text-foreground">Everything You Need,</span>
            <br />
            <span className="bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
              One Swipe Away
            </span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto text-pretty">
            Powerful features designed to make your Windows experience faster, more intuitive, and visually stunning.
          </p>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} feature={feature} index={index} />
          ))}
        </motion.div>
      </div>
    </section>
  )
}
