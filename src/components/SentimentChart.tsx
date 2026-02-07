'use client';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

interface Props {
    positive: number;
    negative: number;
    neutral: number;
}

export default function SentimentChart({ positive, negative, neutral }: Props) {
    const data = {
        labels: ['Positive', 'Negative', 'Neutral'],
        datasets: [
            {
                data: [positive, negative, neutral],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.8)', // Green
                    'rgba(239, 68, 68, 0.8)', // Red
                    'rgba(148, 163, 184, 0.8)', // Gray
                ],
                borderColor: [
                    'rgba(34, 197, 94, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(148, 163, 184, 1)',
                ],
                borderWidth: 1,
                hoverOffset: 4,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom' as const,
                labels: {
                    color: '#cbd5e1',
                    font: {
                        family: "'Outfit', sans-serif",
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleColor: '#e2e8f0',
                bodyColor: '#cbd5e1',
                padding: 12,
                cornerRadius: 8,
                displayColors: true,
            }
        },
        cutout: '70%',
    };

    return (
        <div style={{ height: '300px', position: 'relative' }}>
            <Doughnut data={data} options={options} />
            <div style={{
                position: 'absolute',
                top: '40%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                pointerEvents: 'none',
            }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: '#f8fafc' }}>
                    {positive + negative + neutral}
                </div>
                <div style={{ fontSize: '0.875rem', color: '#94a3b8' }}>Total Items</div>
            </div>
        </div>
    );
}
