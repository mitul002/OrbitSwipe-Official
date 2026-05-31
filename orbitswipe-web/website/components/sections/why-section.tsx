"use client"

import { motion } from "framer-motion"
import { MousePointer, Layers, Gauge, Gem } from "lucide-react"

const reasons = [
  {
    icon: MousePointer,
    title: "Zero Travel Time",
    description: "Opens exactly where your mouse is. No reaching for corners or taskbars.",
    gradient: "from-purple-500 to-violet-600",
  },
  {
    icon: Layers,
    title: "All-in-One Tool",
    description: "Launcher + Window Manager + System Monitor in one elegant interface.",
    gradient: "from-violet-500 to-purple-600",
  },
  {
    icon: Gauge,
    title: "Faster Than Start Menu",
    description: "Replaces the Start Menu with a smarter, quicker system.",
    gradient: "from-blue-500 to-purple-600",
  },
  {
    icon: Gem,
    title: "Premium Experience",
    description: "A visual experience that matches the quality of your workflow.",
    gradient: "from-purple-600 to-pink-500",
  },
]

export function WhySection() {
  return (
    <section className="relative py-32 px-4 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-background to-purple-950/10" />
        <div className="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-purple-950/20 to-transparent" />
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
            Why OrbitSwipe
          </span>
          <h2 className="text-4xl md:text-5xl font-bold">
            <span className="bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
              Built Different
            </span>
          </h2>
        </motion.div>

        {/* Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {reasons.map((reason, index) => (
            <motion.div
              key={reason.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="group"
            >
              <div className="relative p-8 rounded-2xl glass-card h-full hover:border-purple-500/30 transition-all duration-500 overflow-hidden">
                {/* Background gradient on hover */}
                <div className={`absolute inset-0 bg-gradient-to-br ${reason.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`} />
                
                <div className="relative flex items-start gap-5">
                  {/* Icon */}
                  <div className={`shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br ${reason.gradient} p-0.5`}>
                    <div className="w-full h-full rounded-xl bg-background/80 flex items-center justify-center">
                      <reason.icon className="w-6 h-6 text-purple-400" />
                    </div>
                  </div>

                  {/* Content */}
                  <div>
                    <h3 className="text-xl font-semibold text-foreground mb-2 group-hover:text-purple-300 transition-colors">
                      {reason.title}
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {reason.description}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
