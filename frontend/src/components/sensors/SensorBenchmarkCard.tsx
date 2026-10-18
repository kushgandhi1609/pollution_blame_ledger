import React from 'react';
import { CheckCircle2, AlertCircle, ShieldAlert, Cpu } from 'lucide-react';
import { SensorValidationReport } from '../../types';
import { Badge } from '../common/Badge';

interface SensorBenchmarkCardProps {
  validation: SensorValidationReport | null;
}

export const SensorBenchmarkCard: React.FC<SensorBenchmarkCardProps> = ({ validation }) => {
  if (!validation) return null;

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface-alt)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: '18px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '8px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-primary)',
            }}
          >
            <Cpu size={18} />
          </div>
          <div>
            <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-heading)', margin: 0 }}>
              Synthetic Fault Injection Benchmark
            </h4>
            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
              Validation benchmark injecting synthetic calibration drifts and inlet drops into untouched station subsets.
            </div>
          </div>
        </div>

        <Badge variant={validation.benchmark_passed ? 'active' : 'warning'} size="md">
          {validation.benchmark_passed ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
          {validation.benchmark_passed ? 'BENCHMARK PASSED' : 'UNDER REVIEW'}
        </Badge>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
        }}
      >
        <div style={{ padding: '10px 14px', backgroundColor: 'var(--color-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Detection Rate (Recall)</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-active-text)' }}>
            {validation.detection_rate_pct}%
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>Target threshold: ≥ 80.0%</div>
        </div>

        <div style={{ padding: '10px 14px', backgroundColor: 'var(--color-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>False-Alarm Rate</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-primary)' }}>
            {validation.false_alarm_rate_pct}%
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>Target ceiling: ≤ 10.0%</div>
        </div>

        <div style={{ padding: '10px 14px', backgroundColor: 'var(--color-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Injected Fault Stations</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-heading)' }}>
            {validation.injected_fault_stations} Test Stations
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>+45% drift & inlet drop</div>
        </div>

        <div style={{ padding: '10px 14px', backgroundColor: 'var(--color-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Untouched Monitors</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-heading)' }}>
            {validation.untouched_stations} Baseline Stations
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>Tested for false alarm stability</div>
        </div>
      </div>
    </div>
  );
};
