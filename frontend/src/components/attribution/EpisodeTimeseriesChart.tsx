import React from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { EpisodeTimeseriesPoint } from '../../types';

interface EpisodeTimeseriesChartProps {
  timeseries: EpisodeTimeseriesPoint[];
  episodeTitle: string;
}

export const EpisodeTimeseriesChart: React.FC<EpisodeTimeseriesChartProps> = ({
  timeseries,
  episodeTitle,
}) => {
  if (!timeseries || timeseries.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No hourly telemetry records for this window.
      </div>
    );
  }

  // Sample or format timeseries points
  const formatted = timeseries.map((pt) => {
    const d = new Date(pt.time);
    const dateStr = !isNaN(d.getTime())
      ? `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:00`
      : pt.time;

    return {
      time: dateStr,
      pm25: pt.delhi_pm25_hourly_mean !== undefined ? Math.round(pt.delhi_pm25_hourly_mean) : null,
      wind_speed: pt.wind_speed_m_s !== undefined ? Number(pt.wind_speed_m_s.toFixed(1)) : null,
      fires: pt.fires_linked_median || 0,
      stagnation: pt.stagnation_day === 1 ? 1 : 0,
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
          <h4
            style={{
              fontSize: '15px',
              fontWeight: 600,
              color: 'var(--color-heading)',
              margin: 0,
            }}
          >
            Atmospheric & Transport Dynamics (Hourly Telemetry)
          </h4>
          <p
            style={{
              fontSize: '12px',
              color: 'var(--color-text-muted)',
              marginTop: '2px',
              marginBottom: 0,
            }}
          >
            {episodeTitle} • Tracking PM2.5 spikes against surface wind speeds and VIIRS satellite fire corridors.
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
                height: '3px',
                backgroundColor: 'var(--color-primary)',
              }}
            />
            <span>Delhi PM2.5 (µg/m³)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                width: '12px',
                height: '3px',
                backgroundColor: '#D97706',
              }}
            />
            <span>Wind Speed (m/s)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                width: '10px',
                height: '10px',
                backgroundColor: '#8C5032',
                borderRadius: '2px',
              }}
            />
            <span>Corridor Fire Detections</span>
          </div>
        </div>
      </div>

      <div style={{ height: '300px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formatted} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: 'var(--color-text-secondary)' }}
              interval="preserveStartEnd"
              angle={-25}
              textAnchor="end"
              height={45}
            />
            {/* Left Axis: PM2.5 */}
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }}
              domain={[0, 'auto']}
              unit=" µg"
            />
            {/* Right Axis: Wind Speed & Fires */}
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: '#D97706' }}
              domain={[0, 'auto']}
              unit=" m/s"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-surface)',
                borderColor: 'var(--color-border-card)',
                boxShadow: 'var(--shadow-md)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '12px',
              }}
            />
            <Bar
              yAxisId="left"
              dataKey="fires"
              fill="rgba(140, 80, 50, 0.35)"
              name="Satellite Fire Counts"
              barSize={8}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="pm25"
              stroke="var(--color-primary)"
              strokeWidth={2}
              dot={false}
              name="Delhi PM2.5"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="wind_speed"
              stroke="#D97706"
              strokeWidth={1.5}
              strokeDasharray="4 2"
              dot={false}
              name="Wind Speed"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
