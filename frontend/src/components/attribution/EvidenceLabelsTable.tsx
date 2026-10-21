import React from 'react';
import { ShieldCheck, AlertTriangle, HelpCircle } from 'lucide-react';
import { EvidenceLabel } from '../../types';
import { Badge } from '../common/Badge';

interface EvidenceLabelsTableProps {
  labels: EvidenceLabel[];
}

const sourceLabels: Record<string, string> = {
  stubble_burning: 'Agricultural Stubble Burning',
  vehicular: 'Vehicular Traffic Exhaust',
  dust: 'Road Silt & Construction Dust',
  industry: 'Industrial Boilers & Fuel Oil',
  other: 'Secondary Aerosols & Other Remainder',
};

export const EvidenceLabelsTable: React.FC<EvidenceLabelsTableProps> = ({ labels }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div>
        <h4
          style={{
            fontSize: '15px',
            fontWeight: 600,
            color: 'var(--color-heading)',
            margin: 0,
          }}
        >
          Multi-Sensor Evidence Confidence & Cross-Validation
        </h4>
        <p
          style={{
            fontSize: '12px',
            color: 'var(--color-text-muted)',
            marginTop: '2px',
            marginBottom: 0,
          }}
        >
          Every attribution is verified against independent physical tracers (satellite FRP, boundary layer height, NO2/CO ratios) to prevent false conviction.
        </p>
      </div>

      <div
        style={{
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden',
          backgroundColor: 'var(--color-surface)',
        }}
      >
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '12px',
            textAlign: 'left',
          }}
        >
          <thead>
            <tr style={{ backgroundColor: 'var(--color-th-bg)', borderBottom: '1px solid var(--color-border)' }}>
              <th style={{ padding: '12px 16px', color: 'var(--color-th-text)', fontWeight: 600, width: '22%' }}>
                Source Category
              </th>
              <th style={{ padding: '12px 16px', color: 'var(--color-th-text)', fontWeight: 600, width: '12%' }}>
                Midpoint Share
              </th>
              <th style={{ padding: '12px 16px', color: 'var(--color-th-text)', fontWeight: 600, width: '18%' }}>
                Confidence Grade
              </th>
              <th style={{ padding: '12px 16px', color: 'var(--color-th-text)', fontWeight: 600, width: '48%' }}>
                Empirical Support & Scientific Rationale
              </th>
            </tr>
          </thead>
          <tbody>
            {labels.map((row) => {
              const labelStr = row.label || 'Insufficient evidence';
              let badgeVariant: 'active' | 'warning' | 'onboard' = 'onboard';
              let Icon = HelpCircle;
              let confidenceGrade = '';

              // Better matching for confidence grades
              const lowLabel = labelStr.toLowerCase();

              if (
                lowLabel.includes('supported') ||
                lowLabel.includes('strong') ||
                lowLabel.includes('high') ||
                lowLabel.includes('winds from stubble belt') ||
                lowLabel.includes('trapping urban fleet emissions') ||
                lowLabel.includes('secondary inorganic aerosol')
              ) {
                badgeVariant = 'active';
                Icon = ShieldCheck;
                confidenceGrade = 'Supported';
              } else {
                badgeVariant = 'warning';
                Icon = AlertTriangle;
                confidenceGrade = 'Insufficient Evidence';
              }

              return (
                <tr
                  key={row.source}
                  style={{
                    borderBottom: '1px solid var(--color-border-light)',
                    transition: 'background-color 0.1s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-row-hover)')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <td style={{ padding: '12px 16px', verticalAlign: 'top' }}>
                    <Badge sourceKey={row.source} size="sm">
                      {sourceLabels[row.source] || row.source}
                    </Badge>
                  </td>

                  <td style={{ padding: '12px 16px', verticalAlign: 'top', fontWeight: 700, color: 'var(--color-heading)' }}>
                    {row.share_mid_pct ? `${row.share_mid_pct.toFixed(1)}%` : '—'}
                  </td>

                  <td style={{ padding: '12px 16px', verticalAlign: 'top' }}>
                    <Badge variant={badgeVariant} size="sm">
                      <Icon size={12} />
                      {confidenceGrade}
                    </Badge>
                  </td>

                  <td style={{ padding: '12px 16px', verticalAlign: 'top', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                    {/* Using the label itself as the rationale since that's what's currently in ledger_entries.csv */}
                    <div>{labelStr}</div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
