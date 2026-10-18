import React, { useState } from 'react';
import { ShieldAlert, CheckSquare, AlertCircle, Building2, Eye } from 'lucide-react';
import { ActionRecommendation } from '../../types';
import { Badge } from '../common/Badge';

interface ActionRecommendationsProps {
  actions: ActionRecommendation[];
  episodeTitle?: string;
}

const tierLabels: Record<string, { label: string; variant: 'active' | 'warning' | 'expired' | 'onboard' }> = {
  act: { label: 'Immediate Suppression (ACT)', variant: 'active' },
  assess: { label: 'Corridor Assessment (ASSESS)', variant: 'onboard' },
  inspect: { label: 'Industrial Audit (INSPECT)', variant: 'warning' },
  alert: { label: 'Inter-State Advisory (ALERT)', variant: 'warning' },
  verify: { label: 'Ground Verification (VERIFY)', variant: 'onboard' },
  collect: { label: 'Telemetry Collection (COLLECT)', variant: 'neutral' as any },
};

export const ActionRecommendations: React.FC<ActionRecommendationsProps> = ({
  actions,
  episodeTitle,
}) => {
  const [selectedTier, setSelectedTier] = useState<string>('');

  const filtered = selectedTier
    ? actions.filter((a) => a.tier.toLowerCase() === selectedTier.toLowerCase())
    : actions;

  const tiers = Array.from(new Set(actions.map((a) => a.tier)));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Tier Filter Tabs */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          flexWrap: 'wrap',
          borderBottom: '1px solid var(--color-border)',
          paddingBottom: '12px',
        }}
      >
        <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          Action Tier:
        </span>
        <button
          onClick={() => setSelectedTier('')}
          style={{
            padding: '4px 10px',
            fontSize: '12px',
            fontWeight: 500,
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--color-border)',
            backgroundColor: !selectedTier ? 'var(--color-primary)' : 'var(--color-surface)',
            color: !selectedTier ? '#FFFFFF' : 'var(--color-text-secondary)',
          }}
        >
          All Actions ({actions.length})
        </button>
        {tiers.map((t) => (
          <button
            key={t}
            onClick={() => setSelectedTier(t)}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: selectedTier === t ? 'var(--color-primary)' : 'var(--color-surface)',
              color: selectedTier === t ? '#FFFFFF' : 'var(--color-text-secondary)',
              textTransform: 'uppercase',
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Action Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filtered.map((item, idx) => {
          const tierInfo = tierLabels[item.tier.toLowerCase()] || {
            label: item.tier.toUpperCase(),
            variant: 'neutral',
          };

          return (
            <div
              key={idx}
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border-card)',
                borderRadius: 'var(--radius-md)',
                padding: '16px 20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              {/* Header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Badge variant={tierInfo.variant} size="sm">
                    {tierInfo.label}
                  </Badge>
                  <Badge sourceKey={item.source} size="sm">
                    {item.source.replace('_', ' ')}
                  </Badge>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  <Building2 size={13} />
                  <span>Authority: <strong>{item.responsible_party}</strong></span>
                </div>
              </div>

              {/* Action Description */}
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-heading)', lineHeight: 1.5 }}>
                {item.action}
              </div>

              {/* Verification & Safeguard Checklist */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: '12px',
                  backgroundColor: 'var(--color-surface-alt)',
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '11px',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '3px' }}>
                    <CheckSquare size={13} color="var(--color-primary)" />
                    <span>Mandatory Verification Before Enforcement:</span>
                  </div>
                  <div style={{ color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                    {item.verification_needed}
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, color: 'var(--color-warning-text)', marginBottom: '3px' }}>
                    <AlertCircle size={13} />
                    <span>Regulatory Caution & Safeguard:</span>
                  </div>
                  <div style={{ color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
                    {item.caution}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
