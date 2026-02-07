
// --- Types ---
export interface FeedbackItem {
    id: string;
    text: string;
    sentimentScore: number; // -5 to 5
    sentimentLabel: 'positive' | 'negative' | 'neutral';
    keywords: string[];
    category: string;
}

export interface AnalysisResult {
    totalCount: number;
    averageSentiment: number;
    sentimentDistribution: {
        positive: number;
        negative: number;
        neutral: number;
    };
    topThemes: ThemeCluster[];
    actionableInsights: string[]; // Generated "AI" suggestions
}

export interface ThemeCluster {
    name: string;
    count: number;
    sentiment: number; // Average sentiment for this theme
    examples: string[]; // Top 3 examples
}

// --- Configuration ---
// Keywords map to categories. This mimics a classification model.
const TOPIC_KEYWORDS: Record<string, string[]> = {
    'Pricing & Value': ['price', 'cost', 'expensive', 'cheap', 'subscription', 'plan', 'billing', 'charge', 'value', 'worth'],
    'User Experience (UX)': ['ui', 'ux', 'interface', 'button', 'click', 'menu', 'navigation', 'layout', 'design', 'color', 'dark mode'],
    'Performance & Stability': ['slow', 'lag', 'crash', 'bug', 'error', 'loading', 'fast', 'speed', 'performance', 'stable'],
    'Customer Support': ['support', 'help', 'service', 'chat', 'agent', 'email', 'response', 'rude', 'polite', 'ticket'],
    'Authentication': ['login', 'signup', 'password', 'auth', 'register', 'account', 'email', 'verify', '2fa'],
    'Features': ['feature', 'missing', 'add', 'request', 'option', 'setting', 'customization']
};

const POSITIVE_WORDS = new Set(['great', 'good', 'love', 'amazing', 'excellent', 'best', 'fantastic', 'fast', 'easy', 'helpful', 'nice', 'clean', 'smooth', 'perfect', 'worth', 'cheap', 'value', 'stable', 'secure', 'beautiful', 'fun']);
const NEGATIVE_WORDS = new Set(['bad', 'terrible', 'hate', 'awful', 'worst', 'slow', 'hard', 'difficult', 'confusing', 'ugly', 'bug', 'crash', 'error', 'rude', 'expensive', 'lag', 'failed', 'broken', 'mess', 'annoying', 'boring']);

// --- Core Logic ---

export function analyzeFeedback(texts: string[]): AnalysisResult {
    const items: FeedbackItem[] = texts.map((text) => processSingleFeedback(text));

    // Aggregate stats
    const total = items.length;
    const sentimentSum = items.reduce((acc, item) => acc + item.sentimentScore, 0);
    const avgSentiment = total > 0 ? sentimentSum / total : 0;

    const distribution = {
        positive: items.filter((i) => i.sentimentLabel === 'positive').length,
        negative: items.filter((i) => i.sentimentLabel === 'negative').length,
        neutral: items.filter((i) => i.sentimentLabel === 'neutral').length,
    };

    // Cluster by Theme
    const themes = clusterThemes(items);

    // Generate Insights (Rule-based heuristics to mimic LLM)
    const insights = generateInsights(themes, distribution, avgSentiment);

    return {
        totalCount: total,
        averageSentiment: avgSentiment,
        sentimentDistribution: distribution,
        topThemes: themes,
        actionableInsights: insights,
    };
}

function processSingleFeedback(text: string): FeedbackItem {
    // Simple heuristic sentiment analysis to avoid serverless dependency issues
    const words = text.toLowerCase().match(/\b(\w+)\b/g) || [];
    let score = 0;
    const foundKeywords: string[] = [];

    words.forEach(word => {
        if (POSITIVE_WORDS.has(word)) {
            score += 2;
            foundKeywords.push(word);
        }
        else if (NEGATIVE_WORDS.has(word)) {
            score -= 2;
            foundKeywords.push(word);
        }
    });

    // Determine Category
    let category = 'General';
    let maxMatches = 0;

    for (const [topic, keywords] of Object.entries(TOPIC_KEYWORDS)) {
        const matches = keywords.filter(k => text.toLowerCase().includes(k)).length;
        if (matches > maxMatches) {
            maxMatches = matches;
            category = topic;
        }
    }

    // Determine Label based on Score
    let label: 'positive' | 'negative' | 'neutral' = 'neutral';
    if (score > 0) label = 'positive';
    if (score < 0) label = 'negative';

    return {
        id: Math.random().toString(36).substr(2, 9),
        text,
        sentimentScore: score,
        sentimentLabel: label,
        keywords: foundKeywords,
        category
    };
}

function clusterThemes(items: FeedbackItem[]): ThemeCluster[] {
    const clusters: Record<string, FeedbackItem[]> = {};

    // Group
    items.forEach(item => {
        if (!clusters[item.category]) clusters[item.category] = [];
        clusters[item.category].push(item);
    });

    // Transform to ThemeCluster
    // Only keep top 5 largest clusters
    return Object.entries(clusters)
        .map(([name, group]) => ({
            name,
            count: group.length,
            sentiment: group.reduce((acc, i) => acc + i.sentimentScore, 0) / group.length,
            examples: group.slice(0, 3).map(i => i.text)
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 5);
}

function generateInsights(themes: ThemeCluster[], distribution: { positive: number, negative: number, neutral: number }, avgSentiment: number): string[] {
    const insights: string[] = [];

    // Insight 1: Overall Sentiment
    if (avgSentiment > 0.5) insights.push("🚀 Users generally love the product! Sentiment is strongly positive.");
    else if (avgSentiment < -0.5) insights.push("⚠️ Critical Action Required: Sentiment is trending negative.");
    else insights.push("ℹ️ Product sentiment is mixed/neutral. Users have specific pain points.");

    // Insight 2: Problem Areas
    const problemTheme = themes.find(t => t.sentiment < 0);
    if (problemTheme) {
        insights.push(`🔴 High Negative Signal in "${problemTheme.name}": ${Math.abs(Math.round(problemTheme.sentiment * 10) / 10)} sentiment score. Users are complaining about this area.`);
    }

    // Insight 3: Feature Requests
    const featureTheme = themes.find(t => t.name.includes("Features") || t.name.includes("UX"));
    if (featureTheme && featureTheme.count > 2) {
        insights.push(`✨ ${featureTheme.count} users mentioned UX/Feature requests. Check the feedback for specific ideas.`);
    }

    // Insight 4: Scale
    if (distribution.negative > distribution.positive) {
        insights.push(`📉 Negative feedback outweighs positive by ${Math.round((distribution.negative / distribution.positive) || 0)}x.`);
    }

    return insights;
}
