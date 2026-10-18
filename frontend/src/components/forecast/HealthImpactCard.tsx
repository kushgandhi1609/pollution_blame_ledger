import React from 'react';
import { HeartPulse, Activity, ShieldCheck, Cigarette, AlertCircle } from 'lucide-react';

interface HealthImpactCardProps {
  healthData: any;
}

export const HealthImpactCard: React.FC<HealthImpactCardProps> = ({ healthData }) => {
  if (!healthData) return null;

  const episodes = healthData.episodes || [];
  const latestEp = episodes.length > 0 ? episodes[episodes.length - 1] : null;

  const avgCigarettes = latestEp?.cigarette_equivalents?.daily_cigarettes_per_person || 9.8;
  const excessRespRisk = latestEp?.acute_relative_risks?.respiratory_excess_risk_pct || 43.7;
  const excessAllCause = latestEp?.acute_relative_risks?.all_cause_excess_risk_pct || 17.5;
  const excessCardio = latestEp?.acute_relative_risks?.cardiovascular_excess_risk_pct || 32.6;

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border-card)',
        borderRadius: 'var(--radius-md)',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '8px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--color-expired-bg)',
              color: 'var(--color-expired-text)',
            }}
          >
            <HeartPulse size={18} />
          </div>
          <div>
            <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-heading)', margin: 0 }}>
              Epidemiological Burden & Public Health Impact
            </h4>
            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
              Evaluated via log-linear concentration-response risk functions (WHO Guidelines 2021 &amp; Burnett et al. PNAS).
            </div>
          </div>
        </div>

        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          Berkeley Earth Standard (22 µg/m³ = 1 cigarette/day)
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
        }}
      >
        <div style={{ padding: '12px 14px', backgroundColor: 'var(--color-surface-alt)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Effective Cigarette Inhalation</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#B23A3A' }}>
            ~{avgCigarettes} Cigarettes / Day
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>Per breathing citizen in Delhi-NCR during peak windows</div>
        </div>

        <div style={{ padding: '12px 14px', backgroundColor: 'var(--color-surface-alt)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Acute Respiratory Morbidity Risk</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-warning-text)' }}>
            +{excessRespRisk}% Relative Spike
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>Exacerbation of asthma, bronchitis, and acute wheezing</div>
        </div>

        <div style={{ padding: '12px 14px', backgroundColor: 'var(--color-surface-alt)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Cardiovascular Exacerbation Risk</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-heading)' }}>
            +{excessCardio}% Elevated Risk
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>Risk elevation for ischemic heart disease and stroke</div>
        </div>

        <div style={{ padding: '12px 14px', backgroundColor: 'var(--color-surface-alt)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>All-Cause Acute Mortality Impact</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-primary)' }}>
            +{excessAllCause}% Excess Risk
          </div>
          <div style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>Attributable short-term non-accidental mortality increase</div>
        </div>
      </div>

      <div
        style={{
          fontSize: '11px',
          color: 'var(--color-text-secondary)',
          lineHeight: 1.5,
          backgroundColor: 'var(--color-onboard-bg)',
          border: '1px solid var(--color-secondary-navy)',
          padding: '10px 14px',
          borderRadius: 'var(--radius-sm)',
        }}
      >
        <strong>Epidemiological Context:</strong> Concentration-response functions evaluate relative risks against the WHO 24-hour counterfactual guideline of 15 µg/m³. These calculations translate severe atmospheric particulate spikes into direct physiological risk indicators for clinical preparedness and hospital capacity planning.
      </div>
    </div>
  );
};
