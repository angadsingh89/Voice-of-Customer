'use client';

import { useState } from 'react';
import { analyzeFeedback, AnalysisResult } from '@/lib/analyzer';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { Wand2, LayoutDashboard, MessageSquareText, FileText, ArrowRight } from 'lucide-react';

const SentimentChart = dynamic(() => import('@/components/SentimentChart'), { ssr: false });
const ThemeList = dynamic(() => import('@/components/ThemeList'), { ssr: false });

const EXAMPLE_FEEDBACK = [
  "I love the new dark mode, it looks amazing!",
  "The app crashes every time I try to upload a photo on Android.",
  "Customer support is terrible, no one replies to my tickets.",
  "Pricing is too high for the value provided.",
  "The login screen is confusing, I can't find the forgot password link.",
  "Great performance improvements in the latest update!",
  "Please add an export to CSV feature.",
  "The interface is clean but a bit hard to navigate on mobile.",
  "Billing is a nightmare, I got charged twice.",
  "Best app I've used for productivity this year."
].join('\n');

export default function Home() {
  const [input, setInput] = useState(EXAMPLE_FEEDBACK);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!input.trim()) return;
    setLoading(true);

    // Simulate AI "Thinking" time for effect
    await new Promise(resolve => setTimeout(resolve, 800));

    // Process
    const lines = input.split('\n').filter(line => line.trim().length > 0);
    const analysis = analyzeFeedback(lines);

    setResult(analysis);
    setLoading(false);
  };

  return (
    <main className="min-h-screen p-4 md:p-8">
      <div className="container mx-auto max-w-6xl">

        {/* Header */}
        <header className="mb-12 text-center relative">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium mb-4">
              <Wand2 size={14} />
              <span>AI-Powered Insights</span>
            </div>

            <h1 className="text-4xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-indigo-400 mb-4 tracking-tight">
              Voice of Customer
            </h1>

            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              Transform messy feedback into actionable product strategy.
              Paste reviews, tweets, or support tickets below.
            </p>
          </motion.div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

          {/* Input Section */}
          <motion.div
            className="lg:col-span-5 flex flex-col gap-4"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="glass-card p-6 h-full flex flex-col relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500"></div>

              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <MessageSquareText className="text-indigo-400" size={20} />
                  Raw Feedback
                </h2>
                <span className="text-xs text-slate-500">{input.split('\n').length} items</span>
              </div>

              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Paste feedback here (one per line)..."
                className="input-area flex-1 bg-slate-900/50 border border-slate-700/50 rounded-lg p-4 text-slate-300 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all resize-none mb-4 font-mono text-sm leading-relaxed"
                spellCheck={false}
              />

              <button
                onClick={handleAnalyze}
                disabled={loading || !input.trim()}
                className={`btn-primary w-full justify-center py-4 text-lg shadow-lg shadow-indigo-500/20 group relative overflow-hidden ${loading ? 'opacity-80 cursor-wait' : ''}`}
              >
                <span className="relative z-10 flex items-center gap-2">
                  {loading ? (
                    <>Analyzing...</>
                  ) : (
                    <>Generate Insights <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></>
                  )}
                </span>
                {/* Shiny effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              </button>
            </div>
          </motion.div>

          {/* Results Section */}
          <div className="lg:col-span-7 space-y-6">
            {!result && !loading && (
              <motion.div
                className="h-full flex flex-col items-center justify-center p-12 glass-card border-dashed border-slate-700"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                <LayoutDashboard size={64} className="text-slate-700 mb-4" />
                <p className="text-slate-500 text-center">
                  Insights will appear here after analysis.
                </p>
              </motion.div>
            )}

            {result && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="space-y-6"
              >

                {/* 1. Key Metrics Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Sentiment Chart */}
                  <div className="glass-card p-6 flex flex-col items-center justify-center min-h-[300px]">
                    <h3 className="text-lg font-semibold mb-6 text-slate-200 w-full text-left border-b border-slate-700 pb-2">Sentiment Distribution</h3>
                    <div className="w-48 h-48 relative">
                      <SentimentChart
                        positive={result.sentimentDistribution.positive}
                        negative={result.sentimentDistribution.negative}
                        neutral={result.sentimentDistribution.neutral}
                      />
                    </div>
                  </div>

                  {/* AI Insights Panel */}
                  <div className="glass-card p-6 flex flex-col relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5">
                      <Wand2 size={120} />
                    </div>
                    <h3 className="text-lg font-semibold mb-4 text-indigo-300 flex items-center gap-2">
                      <Wand2 size={18} />
                      AI Executive Summary
                    </h3>
                    <ul className="space-y-4">
                      {result.actionableInsights.map((insight, idx) => (
                        <motion.li
                          key={idx}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.2 + (idx * 0.1) }}
                          className="flex items-start gap-3 text-sm text-slate-300 leading-relaxed bg-slate-800/30 p-3 rounded-lg border border-slate-700/50"
                        >
                          <span className="mt-1 translate-y-[2px] w-2 h-2 rounded-full bg-indigo-500 shrink-0" />
                          {insight}
                        </motion.li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 2. Topic Clusters */}
                <div>
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <FileText className="text-purple-400" size={20} />
                    Emerging Themes
                  </h3>
                  <ThemeList themes={result.topThemes} />
                </div>

              </motion.div>
            )}
          </div>

        </div>
      </div>
    </main>
  );
}
