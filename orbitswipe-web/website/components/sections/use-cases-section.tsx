"use client"

import { motion } from "framer-motion"
import { Gamepad2, Code2, Briefcase, Sparkles } from "lucide-react"

const useCases = [
  {
    icon: Gamepad2,
    title: "Gaming",
    description: "Adjust volume or pin apps without leaving your game. No alt-tabbing required.",
    color: "text-green-400",
    bg: "bg-green-500/10",
    border: "border-green-500/20",
  },
  {
    icon: Code2,
    title: "Development",
    description: "Launch your full dev environment instantly. IDEs, terminals, browsers in one click.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
  {
    icon: Briefcase,
    title: "Productivity",
    description: "Access tools without breaking focus. Keep your workflow uninterrupted.",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
  },
  {
    icon: Sparkles,
    title: "Minimalists",
    description: "Clean desktop with hidden edge trigger. Everything accessible, nothing visible.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
  },
]

export function UseCasesSection() {
  return (
    <section className="relative py-32 px-4 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-purple-950/10 via-background to-background" />
      
      {/* Decorative orbs */}
      <div className="absolute top-1/3 right-0 w-[400px] h-[400px] bg-purple-600/10 rounded-full blur-[100px] translate-x-1/2" />
      <div className="absolute bottom-1/3 left-0 w-[400px] h-[400px] bg-violet-600/10 rounded-full blur-[100px] -translate-x-1/2" />

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
            Use Cases
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-foreground">Perfect For</span>
            <br />
            <span className="bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
              Every Workflow
            </span>
          </h2>
        </motion.div>

        {/* Use case cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {useCases.map((useCase, index) => (
            <motion.div
              key={useCase.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              whileHover={{ y: -8 }}
              className="group"
            >
              <div className={`relative p-6 rounded-2xl glass-card h-full border ${useCase.border} hover:border-purple-500/40 transition-all duration-300`}>
                {/* Icon */}
                <div className={`w-12 h-12 rounded-xl ${useCase.bg} flex items-center justify-center mb-5`}>
                  <useCase.icon className={`w-6 h-6 ${useCase.color}`} />
                </div>

                {/* Content */}
                <h3 className="text-lg font-semibold text-foreground mb-2 group-hover:text-purple-300 transition-colors">
                  {useCase.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {useCase.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
