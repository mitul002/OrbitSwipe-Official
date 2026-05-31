"use client"

import { motion } from "framer-motion"
import { Check, ShieldCheck, Sparkles, Key, ArrowRight, Star } from "lucide-react"
import { Button } from "@/components/ui/button"
import Script from "next/script"

const PLANS = [
  {
    name: "30-Day Free Trial",
    price: "0",
    period: "30 Days",
    desc: "Experience the fully featured OrbitSwipe standalone launcher completely free for 30 days.",
    features: [
      "Access to all launcher modes (Stats & Media player)",
      "Custom premium glass accents generator",
      "Fully responsive double-ring simulator controls",
      "Quick-access Favorites & Toolbox tracks",
      "Lightweight standalone Windows executable",
      "Complete offline functionality (No background ads)",
    ],
    cta: "Download Trial",
    href: "/OrbitSwipe.exe",
    featured: false,
    badge: "No Card Needed",
  },
  {
    name: "1-Year License",
    price: "9.99",
    period: "1 Year",
    desc: "Enjoy unlimited access to all features of OrbitSwipe for a full year with regular software updates.",
    features: [
      "1 year of unlimited launcher runs",
      "Access to all launcher modes (Stats & Media)",
      "Custom premium glass accents generator",
      "Fully responsive double-ring controls",
      "Quick-access Favorites & Toolbox tracks",
      "Standard software updates for 1 year",
      "Standard email & technical support",
    ],
    cta: "Buy 1-Year Key",
    href: "https://crosstech.lemonsqueezy.com/checkout/buy/a7ebab6d-43c9-4e69-83d1-fd5a587a3827?enabled=1706213",
    featured: false,
    badge: "Flexible Plan",
  },
  {
    name: "Pro Lifetime Key",
    price: "19.99",
    period: "Lifetime",
    desc: "Permanently unlock OrbitSwipe on your device with lifetime access to all core launcher features.",
    features: [
      "Lifetime unlimited launcher runs",
      "Access to all launcher modes (Stats & Media)",
      "Custom premium glass accents generator",
      "Fully responsive double-ring controls",
      "Quick-access Favorites & Toolbox tracks",
      "Flexible device switching support",
      "Lifetime standalone license updates",
    ],
    cta: "Buy Lifetime Key",
    href: "https://crosstech.lemonsqueezy.com/checkout/buy/7e5a61e0-8e1b-4234-873d-30ad2d635981?enabled=1706175",
    featured: true,
    badge: "Best Value",
  },
]

export function PricingSection() {
  return (
    <section id="pricing" className="relative py-32 px-4 overflow-hidden">
      {/* Lemon Squeezy Overlay Loader Script */}
      <Script src="https://assets.lemonsqueezy.com/lemon.js" strategy="lazyOnload" />

      {/* Background gradients */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-b from-background via-purple-950/5 to-background" />
        <div className="absolute top-1/2 left-1/4 w-96 h-96 rounded-full bg-purple-500/10 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-violet-600/10 blur-3xl" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-20"
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium mb-4">
            Transparent Pricing
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="text-white">Activate Your </span>
            <span className="bg-gradient-to-r from-purple-400 via-violet-400 to-purple-500 bg-clip-text text-transparent">
              OrbitSwipe Pro
            </span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto text-pretty">
            Start with our generous 30-day free trial or unlock permanent control with the standalone Pro License.
          </p>
        </motion.div>

        {/* Pricing Cards Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto items-stretch">
          {PLANS.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: i * 0.15 }}
              whileHover={{ y: -8 }}
              className={`relative flex flex-col justify-between rounded-3xl p-8 transition-all duration-300 ${
                plan.featured
                  ? "bg-gradient-to-b from-purple-950/30 via-purple-900/10 to-transparent border-2 border-purple-500/50 shadow-lg shadow-purple-500/10"
                  : "glass-card border border-white/10"
              }`}
            >
              {/* Badge */}
              <div className="absolute top-6 right-6">
                <span
                  className={`text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider ${
                    plan.featured
                      ? "bg-purple-500 text-white shadow-md shadow-purple-500/30 animate-pulse"
                      : "bg-white/5 text-purple-300 border border-purple-500/20"
                  }`}
                >
                  {plan.badge}
                </span>
              </div>

              <div>
                {/* Plan Name */}
                <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                  {plan.featured ? (
                    <Key className="w-5 h-5 text-purple-400" />
                  ) : (
                    <ShieldCheck className="w-5 h-5 text-purple-400" />
                  )}
                  {plan.name}
                </h3>
                <p className="text-sm text-muted-foreground mb-6 min-h-[40px]">
                  {plan.desc}
                </p>

                {/* Price Display */}
                <div className="flex items-baseline gap-1 mb-8">
                  <span className="text-4xl md:text-5xl font-extrabold text-white">
                    ${plan.price}
                  </span>
                  <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                    / {plan.period}
                  </span>
                </div>

                {/* Separator */}
                <div className="w-full h-[1px] bg-white/10 mb-8" />

                {/* Features List */}
                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-sm text-muted-foreground">
                      <div className="w-5 h-5 rounded-full bg-purple-500/20 flex items-center justify-center shrink-0 mt-0.5">
                        <Check className="w-3.5 h-3.5 text-purple-400" />
                      </div>
                      <span className="text-white/85 leading-snug">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Button */}
              <Button
                size="lg"
                className={`w-full py-6 text-base font-semibold group transition-all duration-300 ${
                  plan.featured
                    ? "bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500 border-0 text-white shadow-lg shadow-purple-500/20"
                    : "glass-card border-purple-500/30 hover:border-purple-400/50 hover:bg-purple-500/10 text-purple-300 hover:text-white"
                }`}
                asChild
              >
                <a 
                  href={plan.href} 
                  className={plan.featured ? "lemonsqueezy-button cursor-pointer" : "cursor-pointer"}
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  {plan.cta}
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </a>
              </Button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
