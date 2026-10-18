import React from 'react';
import { ShieldCheck, BookOpen, Layers, CheckCircle2, AlertOctagon } from 'lucide-react';
import { Modal } from '../common/Modal';
import { SourceProfile } from '../../types';
import { Badge } from '../common/Badge';

interface MethodologyModalProps {
  isOpen: boolean;
  onClose: () => void;
  sources: SourceProfile[];
}

export const MethodologyModal: React.FC<MethodologyModalProps> = ({
  isOpen,
  onClose,
  sources,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="AERTRACE Scientific Methodology & Data Dictionary"
      subtitle="Technical documentation of the 5,000-draw Monte Carlo attribution engine, physical tracers, and regulatory safeguards."
      maxWidth="840px"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', fontSize: '13px', lineHeight: 1.6 }}>
        {/* Core Principle Banner */}
        <div
          style={{
            backgroundColor: 'var(--color-onboard-bg)',
            border: '1px solid var(--color-secondary-navy)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
          }}
        >
          <ShieldCheck size={20} color="var(--color-primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: '14px', marginBottom: '4px' }}>
              Core Philosophy: Attribution is an Estimate, Not a Verdict
            </div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: '12px' }}>
              The atmosphere is a dynamic, turbulent fluid. Attribution estimates reflect probabilistic credible ranges calculated across ensemble meteorology and chemical tracers. No single model estimate should be treated as judicial proof or used to penalize commercial or civic entities without independent multi-sensor ground verification.
            </div>
          </div>
        </div>

        {/* 1. Monte Carlo Attribution Engine */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-heading)', marginBottom: '6px' }}>
            1. 5,000-Draw Monte Carlo Ensemble Apportionment
          </h4>
          <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
            Rather than producing misleading single-point deterministic estimates, AerTrace executes 5,000 Monte Carlo draws incorporating:
          </p>
          <ul style={{ paddingLeft: '20px', marginTop: '6px', color: 'var(--color-text-secondary)' }}>
            <li>Lagged ensemble back-trajectories for northwest biomass smoke parcel transport.</li>
            <li>Diurnal traffic congestion indexing coupled with NO2 and CO co-pollutant elevation.</li>
            <li>Coarse particulate mechanical resuspension functions based on soil dryness and wind speed.</li>
            <li>Boundary layer height stagnation penalties that penalize secondary formation during winter inversions.</li>
          </ul>
        </div>

        {/* 2. Modeled Source Profiles */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-heading)', marginBottom: '8px' }}>
            2. Source Profiles & Physical Chemical Tracers
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {sources.map((s) => (
              <div
                key={s.id}
                style={{
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 14px',
                  backgroundColor: 'var(--color-surface-alt)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Badge sourceKey={s.id} size="sm">
                      {s.name} ({s.name_hi})
                    </Badge>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                      Category: {s.category}
                    </span>
                  </div>
                </div>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: '12px', margin: '4px 0 6px 0' }}>
                  {s.description}
                </p>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  <strong>Key Tracers:</strong> {s.tracer_features.join(', ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 3. Spatial IDW Sensor Health Monitor */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-heading)', marginBottom: '6px' }}>
            3. Spatial IDW Sensor Quality Control
          </h4>
          <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
            Every hour, each station's reading is compared against its k=4 nearest neighbors within a 40 km radius using Inverse-Distance Weighting:
          </p>
          <div
            style={{
              backgroundColor: 'var(--color-surface-alt)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              marginTop: '6px',
              fontFamily: 'monospace',
              fontSize: '11px',
              color: 'var(--color-primary)',
            }}
          >
            residual(s, t) = observed_pm25(s, t) - IDW_expected(s, t)
            <br />
            z_score(s, t) = (residual - mean_residual) / std_residual
          </div>
          <p style={{ color: 'var(--color-text-secondary)', marginTop: '6px', fontSize: '12px' }}>
            Stations are flagged as <strong>watch</strong> on moderate divergence, and <strong>suspect</strong> only when deviation persists for $\ge 6$ consecutive hours with weak neighborhood correlation. Raw measurements are never altered or deleted.
          </p>
        </div>

        {/* 4. Regulatory Legal Caution */}
        <div
          style={{
            backgroundColor: 'var(--color-expired-bg)',
            border: '1px solid #F5C7C7',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            fontSize: '12px',
            color: 'var(--color-expired-text)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}
        >
          <AlertOctagon size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong>Legal and Regulatory Safeguard:</strong> This platform is designed strictly for scientific transparency and early civic warning. Judicial actions, financial penalties, or coercive commercial closures must be supported by formal ground regulatory inspections and certified physical filter gravimetry.
          </div>
        </div>
      </div>
    </Modal>
  );
};
