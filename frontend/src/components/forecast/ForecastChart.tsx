import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
} from 'recharts';
import { ForecastHourlyPoint } from '../../types';

interface ForecastChartProps {
  forecastPoints: ForecastHourlyPoint[];
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ forecastPoints }) => {
  const [horizonFilter, setHorizonFilter] = useState<number | null>(null);

  const filtered = horizonFilter
    ? forecastPoints.filter((p) => p.horizon_h === horizonFilter)
    : forecastPoints;

  // Sort ascending by target_time to fix backwards x-axis
  const sorted = [...filtered].sort((a, b) =>
    new Date(a.target_time).getTime() - new Date(b.target_time).getTime()
  );

  // Format data
  const data = sorted.map((pt) => {
    const d = new Date(pt.target_time);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const timeStr = !isNaN(d.getTime())
      ? `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}, ${String(d.getHours()).padStart(2, '0')}:00`
      : pt.target_time;

    return {
      time: timeStr,
      pred: Math.round(pt.pm25_pred),
      low: Math.round(pt.pm25_low),
      high: Math.round(pt.pm25_high),
      observed: pt.delhi_pm25_median !== undefined ? Math.round(pt.delhi_pm25_median) : null,
      category: pt.aqi_category,
    };
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-heading)', margin: 0 }}>
            24-48 Hour PM2.5 Projection with 80% Prediction Interval
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px', marginBottom: 0 }}>
            Gradient boosted model incorporating diurnal boundary layer collapse, upstream fire radiative power, and transport parcel trajectory lags (24h and 48h).
          </p>
          <p style={{ fontSize: '11px', color: 'var(--color-warning-text)', marginTop: '4px', fontStyle: 'italic' }}>
            Note: This demo replays the model on our stored dataset. A live version requires real-time weather forecasts, which is noted as a limitation in the documentation.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setHorizonFilter(null)}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: horizonFilter === null ? 'var(--color-primary)' : 'var(--color-surface)',
              color: horizonFilter === null ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            All Horizons
          </button>
          <button
            onClick={() => setHorizonFilter(24)}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: horizonFilter === 24 ? 'var(--color-primary)' : 'var(--color-surface)',
              color: horizonFilter === 24 ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            24h Horizon
          </button>
          <button
            onClick={() => setHorizonFilter(48)}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: horizonFilter === 48 ? 'var(--color-primary)' : 'var(--color-surface)',
              color: horizonFilter === 48 ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            48h Horizon
          </button>
        </div>
      </div>

      <div style={{ height: '320px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: 'var(--color-text-secondary)' }}
              interval={Math.ceil(data.length / 10)}
              angle={-25}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }}
              domain={[0, 'auto']}
              unit=" µg/m³"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        border: '1px solid var(--color-border-card)',
                        boxShadow: 'var(--shadow-md)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '10px 14px',
                        fontSize: '12px',
                      }}
                    >
                      <div style={{ fontWeight: 600, color: 'var(--color-heading)', marginBottom: '4px' }}>
                        {item.time}
                      </div>
                      <div style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                        Predicted PM2.5: {item.pred} µg/m³
                      </div>
                      <div style={{ color: 'var(--color-text-secondary)', fontSize: '11px' }}>
                        80% Range: {item.low} – {item.high} µg/m³
                      </div>
                      <div style={{ marginTop: '4px', fontSize: '11px', fontWeight: 600, color: 'var(--color-warning-text)' }}>
                        Category: {item.category}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            {/* Uncertainty Area Ribbon */}
            <Area
              type="monotone"
              dataKey="high"
              stroke="none"
              fill="rgba(168, 192, 218, 0.45)"
              name="Upper 90th"
            />
            <Area
              type="monotone"
              dataKey="low"
              stroke="none"
              fill="#FFFFFF"
              name="Lower 10th"
            />
            {/* Projected Mean Curve */}
            <Line
              type="monotone"
              dataKey="pred"
              stroke="var(--color-primary)"
              strokeWidth={2.5}
              dot={{ r: 2 }}
              name="Forecast Midpoint"
            />
            {/* Observed Ground Truth Line */}
            <Line
              type="monotone"
              dataKey="observed"
              stroke="#000000"
              strokeWidth={2}
              dot={false}
              name="Observed PM2.5"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
