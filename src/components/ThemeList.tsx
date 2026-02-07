'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeCluster } from '@/lib/analyzer';

interface Props {
    themes: ThemeCluster[];
}

export default function ThemeList({ themes }: Props) {
    if (themes.length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                No clear themes emerged yet. Try adding more specific feedback.
            </div>
        );
    }

    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
            <AnimatePresence>
                {themes.map((theme, index) => (
                    <motion.div
                        key={theme.name}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        className="glass-card"
                        style={{ padding: '1.5rem', position: 'relative', overflow: 'hidden' }}
                    >
                        {/* Background Accent */}
                        <div style={{
                            position: 'absolute',
                            top: '-50px',
                            right: '-50px',
                            width: '100px',
                            height: '100px',
                            background: theme.sentiment > 0
                                ? 'radial-gradient(circle, rgba(34, 197, 94, 0.2), transparent 70%)'
                                : 'radial-gradient(circle, rgba(239, 68, 68, 0.2), transparent 70%)',
                            zIndex: 0
                        }} />

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', position: 'relative', zIndex: 1 }}>
                            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f1f5f9' }}>{theme.name}</h3>
                            <span className={theme.sentiment > 0 ? 'badge badge-pos' : 'badge badge-neg'}>
                                {theme.sentiment > 0 ? 'Positive' : 'Negative'}
                            </span>
                        </div>

                        <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '1rem' }}>
                            Based on {theme.count} mentions
                        </div>

                        <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', fontSize: '0.85rem' }}>
                            <strong style={{ display: 'block', marginBottom: '0.5rem', color: '#cbd5e1' }}>Example:</strong>
                            <p style={{ fontStyle: 'italic', color: '#94a3b8' }}>"{theme.examples[0]}"</p>
                        </div>
                    </motion.div>
                ))}
            </AnimatePresence>
        </div>
    );
}
