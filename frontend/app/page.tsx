'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function LandingPage() {
  const [activePlan, setActivePlan] = useState<'free' | 'team' | 'enterprise'>('team')

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <span className="text-3xl">🪅</span>
              <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Pinata Code
              </span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-700 hover:text-purple-600 transition-colors">Features</a>
              <a href="#pricing" className="text-gray-700 hover:text-purple-600 transition-colors">Pricing</a>
              <a href="#about" className="text-gray-700 hover:text-purple-600 transition-colors">About</a>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/auth/login" className="text-gray-700 hover:text-purple-600 transition-colors">
                Log in
              </Link>
              <Link
                href="/auth/signup"
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg transition-all"
              >
                Start Free
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-purple-50 via-pink-50 to-white">
        <div className="max-w-6xl mx-auto text-center">
          <div className="text-8xl mb-8 animate-bounce">🪅</div>
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            <span className="bg-gradient-to-r from-purple-600 via-pink-600 to-red-500 bg-clip-text text-transparent">
              It's What's Inside
            </span>
            <br />
            <span className="text-gray-900">That Counts</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Automated workflow scanning for your codebase. Discover patterns, track migrations,
            and understand your code's evolution—all without changing a single line.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link
              href="/auth/signup"
              className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-lg font-semibold rounded-lg hover:shadow-2xl transition-all transform hover:scale-105"
            >
              Start Free Trial
            </Link>
            <a
              href="#pricing"
              className="px-8 py-4 bg-white text-purple-600 text-lg font-semibold rounded-lg border-2 border-purple-600 hover:bg-purple-50 transition-all"
            >
              View Pricing
            </a>
          </div>
          <p className="text-sm text-gray-500">
            No credit card required • 10 free scans per month • Cancel anytime
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-4">
            Built for Everyone
          </h2>
          <p className="text-xl text-gray-600 text-center mb-16 max-w-3xl mx-auto">
            Whether you're a solo developer, a growing team, or an enterprise organization,
            Pinata Code adapts to your workflow scanning needs.
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Individual Developers */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl p-8 hover:shadow-xl transition-all">
              <div className="text-5xl mb-4">👤</div>
              <h3 className="text-2xl font-bold mb-4 text-purple-900">Individual Developers</h3>
              <p className="text-gray-700 mb-6">
                Perfect for freelancers and solo developers managing personal projects or client codebases.
              </p>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start">
                  <span className="text-purple-600 mr-2">✓</span>
                  <span>Scan up to 1 repository</span>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-600 mr-2">✓</span>
                  <span>10 scans per month</span>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-600 mr-2">✓</span>
                  <span>Basic workflow detection</span>
                </li>
                <li className="flex items-start">
                  <span className="text-purple-600 mr-2">✓</span>
                  <span>Export to JSON/CSV</span>
                </li>
              </ul>
              <Link
                href="/auth/signup?plan=free"
                className="mt-8 block w-full text-center px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all font-semibold"
              >
                Start Free
              </Link>
            </div>

            {/* Teams */}
            <div className="bg-gradient-to-br from-pink-50 to-pink-100 rounded-2xl p-8 hover:shadow-xl transition-all border-4 border-pink-400 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-pink-500 text-white px-4 py-1 rounded-full text-sm font-bold">
                MOST POPULAR
              </div>
              <div className="text-5xl mb-4">👥</div>
              <h3 className="text-2xl font-bold mb-4 text-pink-900">Teams</h3>
              <p className="text-gray-700 mb-6">
                Collaborate with your team on multiple repositories with advanced scanning and insights.
              </p>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start">
                  <span className="text-pink-600 mr-2">✓</span>
                  <span>Scan up to 10 repositories</span>
                </li>
                <li className="flex items-start">
                  <span className="text-pink-600 mr-2">✓</span>
                  <span>1,000 scans per month</span>
                </li>
                <li className="flex items-start">
                  <span className="text-pink-600 mr-2">✓</span>
                  <span>Advanced pattern detection</span>
                </li>
                <li className="flex items-start">
                  <span className="text-pink-600 mr-2">✓</span>
                  <span>Team collaboration tools</span>
                </li>
                <li className="flex items-start">
                  <span className="text-pink-600 mr-2">✓</span>
                  <span>Priority support</span>
                </li>
              </ul>
              <Link
                href="/auth/signup?plan=team"
                className="mt-8 block w-full text-center px-6 py-3 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-all font-semibold"
              >
                Start 14-Day Trial
              </Link>
            </div>

            {/* Enterprise */}
            <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-2xl p-8 hover:shadow-xl transition-all">
              <div className="text-5xl mb-4">🏢</div>
              <h3 className="text-2xl font-bold mb-4 text-red-900">Enterprise</h3>
              <p className="text-gray-700 mb-6">
                For large organizations with complex codebases and compliance requirements.
              </p>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">✓</span>
                  <span>Unlimited repositories</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">✓</span>
                  <span>Unlimited scans</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">✓</span>
                  <span>Custom workflow rules</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">✓</span>
                  <span>SSO & RBAC</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">✓</span>
                  <span>Dedicated support</span>
                </li>
              </ul>
              <Link
                href="/auth/signup?plan=enterprise"
                className="mt-8 block w-full text-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all font-semibold"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-gray-50 to-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-gray-600 text-center mb-16 max-w-3xl mx-auto">
            Start free and scale as you grow. No hidden fees, no surprises.
          </p>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free Plan */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border-2 border-gray-200">
              <h3 className="text-2xl font-bold mb-2">Free</h3>
              <div className="mb-6">
                <span className="text-5xl font-bold">$0</span>
                <span className="text-gray-600">/month</span>
              </div>
              <ul className="space-y-4 mb-8 text-gray-700">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>1 repository</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>10 scans/month</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Basic patterns</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Community support</span>
                </li>
              </ul>
              <Link
                href="/auth/signup?plan=free"
                className="block w-full text-center px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-all font-semibold"
              >
                Get Started
              </Link>
            </div>

            {/* Team Plan */}
            <div className="bg-white rounded-2xl p-8 shadow-2xl border-4 border-pink-500 relative transform scale-105">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-pink-500 text-white px-4 py-1 rounded-full text-sm font-bold">
                BEST VALUE
              </div>
              <h3 className="text-2xl font-bold mb-2">Team</h3>
              <div className="mb-6">
                <span className="text-5xl font-bold">$49</span>
                <span className="text-gray-600">/month</span>
              </div>
              <ul className="space-y-4 mb-8 text-gray-700">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>10 repositories</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>1,000 scans/month</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Advanced patterns</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Team collaboration</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Priority support</span>
                </li>
              </ul>
              <Link
                href="/auth/signup?plan=team"
                className="block w-full text-center px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-xl transition-all font-semibold"
              >
                Start 14-Day Trial
              </Link>
            </div>

            {/* Enterprise Plan */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border-2 border-gray-200">
              <h3 className="text-2xl font-bold mb-2">Enterprise</h3>
              <div className="mb-6">
                <span className="text-5xl font-bold">$499</span>
                <span className="text-gray-600">/month</span>
              </div>
              <ul className="space-y-4 mb-8 text-gray-700">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Unlimited repos</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Unlimited scans</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Custom patterns</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>SSO & RBAC</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Dedicated support</span>
                </li>
              </ul>
              <Link
                href="/auth/signup?plan=enterprise"
                className="block w-full text-center px-6 py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-all font-semibold"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">
            How It Works
          </h2>
          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                🔗
              </div>
              <h3 className="text-xl font-bold mb-2">1. Connect</h3>
              <p className="text-gray-600">Link your GitHub repositories with one click</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                🔍
              </div>
              <h3 className="text-xl font-bold mb-2">2. Scan</h3>
              <p className="text-gray-600">Automated workflow pattern detection runs instantly</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                📊
              </div>
              <h3 className="text-xl font-bold mb-2">3. Analyze</h3>
              <p className="text-gray-600">View insights about your codebase patterns</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">
                📈
              </div>
              <h3 className="text-xl font-bold mb-2">4. Track</h3>
              <p className="text-gray-600">Monitor migrations and workflow evolution over time</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-purple-600 via-pink-600 to-red-500">
        <div className="max-w-4xl mx-auto text-center text-white">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Discover What's Inside?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Join developers and teams already using Pinata Code to understand their codebases better.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/auth/signup"
              className="px-8 py-4 bg-white text-purple-600 text-lg font-semibold rounded-lg hover:shadow-2xl transition-all transform hover:scale-105"
            >
              Start Free Trial
            </Link>
            <a
              href="/demo"
              className="px-8 py-4 bg-transparent text-white text-lg font-semibold rounded-lg border-2 border-white hover:bg-white hover:text-purple-600 transition-all"
            >
              Watch Demo
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-3xl">🪅</span>
                <span className="text-xl font-bold">Pinata Code</span>
              </div>
              <p className="text-gray-400 text-sm">
                It's what's inside that counts
              </p>
            </div>
            <div>
              <h4 className="font-bold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="/demo" className="hover:text-white transition-colors">Demo</a></li>
                <li><a href="/docs" className="hover:text-white transition-colors">Documentation</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="/about" className="hover:text-white transition-colors">About</a></li>
                <li><a href="/blog" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="/careers" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="/contact" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="/privacy" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="/terms" className="hover:text-white transition-colors">Terms of Service</a></li>
                <li><a href="/security" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-gray-400 text-sm">
            <p>&copy; 2025 Pinata Code. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
