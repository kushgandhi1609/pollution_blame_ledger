import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { LedgerEntry } from '../../types';
import { Badge } from '../common/Badge';

interface AttributionIntervalChartProps {
  attribution: LedgerEntry[];
  episodeTitle: string;
}

const sourceLabels: Record<string, string> = {
  stubble_burning: 'Agricultural Stubble Burning',
  vehicular: 'Vehicular Traffic Exhaust',
  dust: 'Road Silt & Construction Dust',
  industry: 'Industrial Boilers & Fuel Oil',
  other: 'Secondary Aerosols & Other Remainder',
};

const sourceColors: Record<string, string> = {
  stubble_burning: 'var(--color-source-stubble)',
  vehicular: 'var(--color-source-vehicular)',
  dust: 'var(--color-source-dust)',
  industry: 'var(--color-source-industry)',
  other: 'var(--color-source-other)',
};

export const AttributionIntervalChart: React.FC<AttributionIntervalChartProps> = ({
  attribution,
  episodeTitle,
}) => {
  // Sort by share_mid_pct descending
  const sorted = [...attribution].sort((a, b) => b.share_mid_pct - a.share_mid_pct);

  const chartData = sorted.map((row) => ({
    sourceKey: row.source,
    name: sourceLabels[row.source] || row.source,
    low: Number(row.share_low_pct.toFixed(1)),
    mid: Number(row.share_mid_pct.toFixed(1)),
    high: Number(row.share_high_pct.toFixed(1)),
    spread: Number((row.share_high_pct - row.share_low_pct).toFixed(1)),
    cf_pm25: row.counterfactual_mean_pm25,
    cf_red: row.counterfactual_reduction_pct,
  }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
          <h4
            style={{
              fontSize: '15px',
              fontWeight: 600,
              color: 'var(--color-heading)',
              margin: 0,
            }}
          >
            5,000-Draw Monte Carlo Credible Intervals (10th – 90th Percentile)
          </h4>
          <p
            style={{
              fontSize: '12px',
              color: 'var(--color-text-muted)',
              marginTop: '2px',
              marginBottom: 0,
            }}
          >
            {episodeTitle} • Shaded bars depict attribution uncertainty ranges; solid markers indicate midpoint estimates.
          </p>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            fontSize: '11px',
            color: 'var(--color-text-secondary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                width: '12px',
                height: '12px',
                backgroundColor: 'var(--color-primary)',
                borderRadius: '2px',
              }}
            />
            <span>Midpoint Estimate</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                width: '24px',
                height: '8px',
                backgroundColor: 'var(--color-secondary-navy)',
                borderRadius: '2px',
                opacity: 0.6,
              }}
            />
            <span>10th–90th Credible Range</span>
          </div>
        </div>
      </div>

      {/* Interval Chart Container */}
      <div style={{ height: '240px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 10, right: 30, left: 160, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--color-border)" />
            <XAxis
              type="number"
              domain={[0, (dataMax: number) => Math.min(100, Math.ceil((dataMax + 10) / 10) * 10)]}
              unit="%"
              tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 12, fill: 'var(--color-heading)', fontWeight: 500 }}
              width={160}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div
                      style={{
                        backgroundColor: 'var(--color-surface)',
                        border: '1px solid var(--color-border-card)',
                        boxShadow: 'var(--shadow-md)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '12px',
                        fontSize: '12px',
                      }}
                    >
                      <div
                        style={{
                          fontWeight: 600,
                          color: 'var(--color-heading)',
                          marginBottom: '6px',
                        }}
                      >
                        {data.name}
                      </div>
                      <div style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                        Midpoint: {data.mid}%
                      </div>
                      <div style={{ color: 'var(--color-text-secondary)' }}>
                        Credible Range: {data.low}% – {data.high}%
                      </div>
                      <div style={{ color: 'var(--color-text-dim)', fontSize: '11px', marginTop: '4px' }}>
                        Uncertainty Spread: ±{(data.spread / 2).toFixed(1)}%
                      </div>
                      {data.cf_red && (
                        <div
                          style={{
                            marginTop: '6px',
                            paddingTop: '6px',
                            borderTop: '1px solid var(--color-border)',
                            color: 'var(--color-active-text)',
                            fontWeight: 600,
                          }}
                        >
                          Counterfactual: -{data.cf_red.toFixed(1)}% PM2.5 if curbed
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine x={0} stroke="var(--color-border)" />
            {/* The mid bar */}
            <Bar
              dataKey="mid"
              fill="var(--color-primary)"
              radius={[0, 4, 4, 0]}
              barSize={18}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Numerical Ledger Breakdown Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
        }}
      >
        {sorted.map((item) => (
          <div
            key={item.source}
            style={{
              padding: '12px 14px',
              backgroundColor: 'var(--color-surface-alt)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Badge sourceKey={item.source} size="sm">
                {sourceLabels[item.source] || item.source}
              </Badge>
              <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-heading)' }}>
                {item.share_mid_pct.toFixed(1)}%
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '11px',
                color: 'var(--color-text-secondary)',
              }}
            >
              <span>Credible Interval:</span>
              <strong>
                [{item.share_low_pct.toFixed(1)}% – {item.share_high_pct.toFixed(1)}%]
              </strong>
            </div>

            {item.counterfactual_reduction_pct !== undefined && item.counterfactual_reduction_pct !== null && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '11px',
                  color: 'var(--color-active-text)',
                  backgroundColor: 'var(--color-active-bg)',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-xs)',
                  marginTop: '2px',
                }}
              >
                <span>Potential Relief:</span>
                <strong>-{item.counterfactual_reduction_pct.toFixed(1)}% PM2.5</strong>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
