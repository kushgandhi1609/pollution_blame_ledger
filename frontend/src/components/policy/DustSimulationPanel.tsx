import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Sliders, RefreshCw, AlertCircle, TrendingDown } from 'lucide-react';
import { DustDemoResponse, DustSimulationResult } from '../../types';
import { Button } from '../common/Button';
import { api } from '../../services/api';

interface DustSimulationPanelProps {
  initialDemo: DustDemoResponse | null;
}

export const DustSimulationPanel: React.FC<DustSimulationPanelProps> = ({ initialDemo }) => {
  const [shiftHours, setShiftHours] = useState<number>(4);
  const [mistingEff, setMistingEff] = useState<number>(20);
  const [stagnationWeight, setStagnationWeight] = useState<number>(1.5);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simResult, setSimResult] = useState<DustSimulationResult | null>(null);

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      const res = await api.simulateDustShift({
        shift_hours: shiftHours,
        misting_efficiency_pct: mistingEff,
        stagnation_avoidance_weight: stagnationWeight,
      });
      setSimResult(res);
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Build chart dataset
  const chartData = initialDemo?.schedule.map((row) => {
    const simRow = simResult?.schedule.find((s) => s.hour === row.hour);
    return {
      hour: `${row.hour}:00`,
      baseline: row.baseline_dust_index_sum,
      optimized: simRow ? simRow.custom_scheduled_score : row.optimized_dust_index_sum,
      isStagnant: row.hour >= 7 && row.hour <= 10,
    };
  }) || [];

  const currentReduction = simResult
    ? simResult.achieved_peak_reduction_pct
    : initialDemo?.peak_reduction_pct || 28.4;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--color-heading)', margin: 0 }}>
              Construction Dust Rescheduler & Misting Simulator
            </h4>
            <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '2px', marginBottom: 0 }}>
              Hotspot demonstration (Anand Vihar cluster): Simulates diurnal task shifting from shallow morning inversion to ventilated afternoon windows.
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'var(--color-active-bg)',
              color: 'var(--color-active-text)',
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              fontWeight: 700,
            }}
          >
            <TrendingDown size={16} />
            <span>Peak Exposure Reduction: -{currentReduction}%</span>
          </div>
        </div>
      </div>

      {/* Parameter Control Sliders */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          backgroundColor: 'var(--color-surface-alt)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: '16px 20px',
        }}
      >
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
            <span>Diurnal Shift Window:</span>
            <span style={{ color: 'var(--color-primary)' }}>{shiftHours} Hours</span>
          </div>
          <input
            type="range"
            min={1}
            max={8}
            step={1}
            value={shiftHours}
            onChange={(e) => setShiftHours(Number(e.target.value))}
            style={{ width: '100%', cursor: 'pointer' }}
          />
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)', marginTop: '4px' }}>
            Shift heavy excavation from 07:00–10:00 to 12:00–16:00
          </div>
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
            <span>Misting Efficacy:</span>
            <span style={{ color: 'var(--color-primary)' }}>{mistingEff}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={50}
            step={5}
            value={mistingEff}
            onChange={(e) => setMistingEff(Number(e.target.value))}
            style={{ width: '100%', cursor: 'pointer' }}
          />
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)', marginTop: '4px' }}>
            Empirical suppression limit for fine PM2.5 mechanical misting
          </div>
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
            <span>Inversion Avoidance:</span>
            <span style={{ color: 'var(--color-primary)' }}>{stagnationWeight}x</span>
          </div>
          <input
            type="range"
            min={0.5}
            max={3.0}
            step={0.1}
            value={stagnationWeight}
            onChange={(e) => setStagnationWeight(Number(e.target.value))}
            style={{ width: '100%', cursor: 'pointer' }}
          />
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)', marginTop: '4px' }}>
            Penalty multiplier for emissions during shallow boundary layer hours
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <Button
            variant="primary"
            onClick={handleSimulate}
            disabled={isSimulating}
            icon={<RefreshCw size={14} className={isSimulating ? 'spin' : ''} />}
            style={{ width: '100%' }}
          >
            {isSimulating ? 'Simulating...' : 'Run Simulation'}
          </Button>
        </div>
      </div>

      {/* Diurnal Curve Chart */}
      <div style={{ height: '300px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
            <XAxis
              dataKey="hour"
              tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }}
              domain={[0, 'auto']}
              unit=" idx"
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
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
            <Line
              type="monotone"
              dataKey="baseline"
              stroke="#B23A3A"
              strokeWidth={2}
              dot={{ r: 3 }}
              name="Unregulated Baseline Activity"
            />
            <Line
              type="monotone"
              dataKey="optimized"
              stroke="#1E6B45"
              strokeWidth={2.5}
              dot={{ r: 3 }}
              name="Ventilation-Aware Shifted Schedule"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Scientific Note */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px',
          backgroundColor: 'var(--color-onboard-bg)',
          border: '1px solid var(--color-secondary-navy)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 16px',
          fontSize: '11px',
          color: 'var(--color-onboard-text)',
          lineHeight: 1.5,
        }}
      >
        <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <strong>Scientific Principle:</strong> Diurnal reschedulers flatten extreme exposure peaks by shifting heavy mechanical dust generation away from morning calm hours (when dispersion height is low). It optimizes atmospheric ventilation capacity; it does not eliminate net atmospheric mass.
        </div>
      </div>
    </div>
  );
};
