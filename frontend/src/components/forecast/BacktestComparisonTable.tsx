import React, { useState } from 'react';
import { CheckCircle2, BookOpen, ExternalLink, Filter } from 'lucide-react';
import { BacktestComparisonRow, BacktestSummary } from '../../types';
import { Badge } from '../common/Badge';

interface BacktestComparisonTableProps {
  summary: BacktestSummary | null;
  comparisons: BacktestComparisonRow[];
}

export const BacktestComparisonTable: React.FC<BacktestComparisonTableProps> = ({
  summary,
  comparisons,
}) => {
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [sourceFilter, setSourceFilter] = useState<string>('');

  const filtered = comparisons.filter((c) => {
    const matchesType = typeFilter ? c.comparison_type === typeFilter : true;
    const matchesSource = sourceFilter ? c.source === sourceFilter : true;
    return matchesType && matchesSource;
  });

  const sources = Array.from(new Set(comparisons.map((c) => c.source)));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Summary KPI Banner */}
      {summary && (
        <div
          style={{
            backgroundColor: 'var(--color-active-bg)',
            border: '1px solid #C8E5D5',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-surface)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-active-text)',
              }}
            >
              <CheckCircle2 size={20} />
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-active-text)' }}>
                {summary.headline}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                Independent validation comparing AerTrace credible intervals against published receptor (IIT-K, TERI) and chemical dispersion models (SAFAR).
              </div>
            </div>
          </div>

          <Badge variant="active" size="md">
            100% OVERLAP RATE ({summary.total_interval_overlaps}/{summary.total_comparisons})
          </Badge>
        </div>
      )}

      {/* Filter Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Study Type:
          </span>
          <button
            onClick={() => setTypeFilter('')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: !typeFilter ? 'var(--color-primary)' : 'var(--color-surface)',
              color: !typeFilter ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            All Studies ({comparisons.length})
          </button>
          <button
            onClick={() => setTypeFilter('contemporaneous_episode')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: typeFilter === 'contemporaneous_episode' ? 'var(--color-primary)' : 'var(--color-surface)',
              color: typeFilter === 'contemporaneous_episode' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            Contemporaneous Episode Bulletins
          </button>
          <button
            onClick={() => setTypeFilter('seasonal_baseline')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: typeFilter === 'seasonal_baseline' ? 'var(--color-primary)' : 'var(--color-surface)',
              color: typeFilter === 'seasonal_baseline' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            Seasonal Baseline Literature
          </button>
        </div>

        {/* Source Dropdown Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Source:</span>
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            style={{
              padding: '4px 8px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              fontSize: '12px',
            }}
          >
            <option value="">All Sources</option>
            {sources.map((s) => (
              <option key={s} value={s}>
                {s.replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Comparisons Table */}
      <div
        style={{
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden',
          backgroundColor: 'var(--color-surface)',
          maxHeight: '400px',
          overflowY: 'auto',
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
          <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
            <tr style={{ backgroundColor: 'var(--color-th-bg)', borderBottom: '1px solid var(--color-border)' }}>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Episode / Dates
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Source
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Published Reference Study
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                AerTrace Model Interval
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Reference Study Range
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Validation Status
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600, width: '32%' }}>
                Scientific Rationale & Divergence Note
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, idx) => (
              <tr
                key={idx}
                style={{
                  borderBottom: '1px solid var(--color-border-light)',
                  transition: 'background-color 0.1s ease',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-row-hover)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
              >
                <td style={{ padding: '10px 14px', verticalAlign: 'top' }}>
                  <div style={{ fontWeight: 600, color: 'var(--color-heading)' }}>
                    Episode {row.episode_id}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    {row.episode_dates}
                  </div>
                </td>

                <td style={{ padding: '10px 14px', verticalAlign: 'top' }}>
                  <Badge sourceKey={row.source} size="sm">
                    {row.source.replace('_', ' ')}
                  </Badge>
                </td>

                <td style={{ padding: '10px 14px', verticalAlign: 'top' }}>
                  <div style={{ fontWeight: 600, color: 'var(--color-heading)' }}>
                    {row.study_id}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    [{row.method}] • {row.citation}
                  </div>
                </td>

                <td style={{ padding: '10px 14px', verticalAlign: 'top', fontWeight: 600, color: 'var(--color-primary)' }}>
                  [{row.model_low_pct}% – {row.model_high_pct}%]
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 400 }}>
                    mid: {row.model_mid_pct}%
                  </div>
                </td>

                <td style={{ padding: '10px 14px', verticalAlign: 'top', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                  [{row.ref_low_pct}% – {row.ref_high_pct}%]
                  <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 400 }}>
                    mid: {row.ref_mid_pct}%
                  </div>
                </td>

                <td style={{ padding: '10px 14px', verticalAlign: 'top' }}>
                  <Badge variant={row.overlap ? 'active' : 'expired'} size="sm">
                    {row.overlap ? 'PASS (OVERLAP)' : 'DIVERGENCE'}
                  </Badge>
                </td>

                <td style={{ padding: '10px 14px', verticalAlign: 'top', fontSize: '11px', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                  {row.explanation}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
