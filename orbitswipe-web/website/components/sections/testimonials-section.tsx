"use client"

import { motion, useAnimationControls } from "framer-motion"
import { useEffect, useRef } from "react"
import { Star, Quote } from "lucide-react"

const testimonials = [
  {
    name: "Alex K.",
    role: "Game Developer",
    content: "OrbitSwipe changed how I work. Opening tools mid-game without alt-tabbing is a game changer. Literally.",
    rating: 5,
  },
  {
    name: "Sarah M.",
    role: "UI/UX Designer",
    content: "The glass UI is absolutely stunning. Finally a launcher that looks as good as it functions.",
    rating: 5,
  },
  {
    name: "David L.",
    role: "Software Engineer",
    content: "Script execution from the radial menu saved me hours. PowerShell at my fingertips, everywhere.",
    rating: 5,
  },
  {
    name: "Emma R.",
    role: "Content Creator",
    content: "WinTop manager is a must-have for streaming. Keeping my notes visible while gaming is perfect.",
    rating: 5,
  },
  {
    name: "Michael T.",
    role: "Productivity Coach",
    content: "I recommend OrbitSwipe to all my clients. Zero mouse travel time means better ergonomics.",
    rating: 5,
  },
  {
    name: "Lisa W.",
    role: "Data Analyst",
    content: "Workspace groups let me switch between project setups instantly. Huge time saver.",
    rating: 5,
  },
]

function TestimonialCard({ testimonial, index }: { testimonial: typeof testimonials[0]; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="group relative min-w-[320px] md:min-w-[380px]"
    >
      <div className="relative p-6 rounded-2xl glass-card h-full hover:border-purple-500/30 transition-all duration-500">
        {/* Quote icon */}
        <div className="absolute top-4 right-4 opacity-10 group-hover:opacity-20 transition-opacity">
          <Quote className="w-10 h-10 text-purple-400" />
        </div>

        {/* Rating */}
        <div className="flex gap-1 mb-4">
          {[...Array(testimonial.rating)].map((_, i) => (
            <Star key={i} className="w-4 h-4 fill-purple-400 text-purple-400" />
          ))}
        </div>

        {/* Content */}
        <p className="text-muted-foreground leading-relaxed mb-6 text-pretty">
          &ldquo;{testimonial.content}&rdquo;
        </p>

        {/* Author */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center text-foreground font-bold">
            {testimonial.name[0]}
          </div>
          <div>
            <div className="font-semibold text-foreground text-sm">{testimonial.name}</div>
            <div className="text-xs text-muted-foreground">{testimonial.role}</div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export function TestimonialsSection() {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const scroll = scrollRef.current
    if (!scroll) return

    let animationId: number
    let position = 0

    const animate = () => {
      position += 0.5
      if (position >= scroll.scrollWidth / 2) {
        position = 0
      }
      scroll.scrollLeft = position
      animationId = requestAnimationFrame(animate)
    }

    animationId = requestAnimationFrame(animate)

    const handleMouseEnter = () => cancelAnimationFrame(animationId)
    const handleMouseLeave = () => {
      animationId = requestAnimationFrame(animate)
    }

    scroll.addEventListener("mouseenter", handleMouseEnter)
    scroll.addEventListener("mouseleave", handleMouseLeave)

    return () => {
      cancelAnimationFrame(animationId)
      scroll.removeEventListener("mouseenter", handleMouseEnter)
      scroll.removeEventListener("mouseleave", handleMouseLeave)
    }
  }, [])

  return (
    <section className="relative py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-background via-purple-950/5 to-background" />
      </div>

      <div className="relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16 px-4"
        >
          <span className="inline-block px-4 py-1.5 rounded-full glass-card text-sm text-purple-300 mb-4">
            Loved by Users
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-foreground">What People</span>{" "}
            <span className="bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
              Are Saying
            </span>
          </h2>
        </motion.div>

        {/* Scrolling testimonials */}
        <div
          ref={scrollRef}
          className="flex gap-6 overflow-x-auto scrollbar-hide px-4"
          style={{ scrollBehavior: "auto" }}
        >
          {/* Double the testimonials for infinite scroll effect */}
          {[...testimonials, ...testimonials].map((testimonial, index) => (
            <TestimonialCard key={index} testimonial={testimonial} index={index % testimonials.length} />
          ))}
        </div>

        {/* Gradient fades */}
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-32 h-full bg-gradient-to-r from-background to-transparent pointer-events-none z-10" />
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-32 h-full bg-gradient-to-l from-background to-transparent pointer-events-none z-10" />
      </div>
    </section>
  )
}
