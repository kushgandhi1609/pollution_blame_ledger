import React from 'react';
import { ForecastEvaluationRow } from '../../types';

interface ForecastEvaluationTableProps {
  evaluation: ForecastEvaluationRow[];
}

export const ForecastEvaluationTable: React.FC<ForecastEvaluationTableProps> = ({ evaluation }) => {
  if (!evaluation || evaluation.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div>
        <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-heading)', margin: 0 }}>
          Forecasting Model Accuracy Benchmark
        </h4>
        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          Evaluated against naive persistence (yesterday's air persists) and historical seasonal mean baselines.
        </div>
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
              <th style={{ padding: '8px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Model / Benchmark
              </th>
              <th style={{ padding: '8px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Horizon
              </th>
              <th style={{ padding: '8px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                RMSE (µg/m³)
              </th>
              <th style={{ padding: '8px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                MAE (µg/m³)
              </th>
              <th style={{ padding: '8px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                R² Score
              </th>
              <th style={{ padding: '8px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                AQI Accuracy
              </th>
            </tr>
          </thead>
          <tbody>
            {evaluation.map((row, idx) => {
              const name = row.method || row.model_name || 'Model';
              const isBest = name.toLowerCase().includes('gradient');
              const rmse = row.rmse_ugm3 ?? row.rmse ?? null;
              const mae = row.mae_ugm3 ?? row.mae ?? null;
              const r2 = row.r2_score ?? row.r2 ?? null;
              const acc = row.aqi_category_acc_pct ?? null;

              return (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid var(--color-border-light)',
                    backgroundColor: isBest ? 'var(--color-active-bg)' : 'transparent',
                  }}
                >
                  <td style={{ padding: '8px 14px', fontWeight: isBest ? 700 : 500, color: isBest ? 'var(--color-active-text)' : 'var(--color-heading)' }}>
                    {name}
                  </td>
                  <td style={{ padding: '8px 14px', color: 'var(--color-text-secondary)' }}>
                    {row.horizon_h} Hours
                  </td>
                  <td style={{ padding: '8px 14px', fontWeight: 600 }}>
                    {rmse !== null ? Number(rmse).toFixed(1) : '—'}
                  </td>
                  <td style={{ padding: '8px 14px', color: 'var(--color-text-secondary)' }}>
                    {mae !== null ? Number(mae).toFixed(1) : '—'}
                  </td>
                  <td style={{ padding: '8px 14px', fontWeight: 700, color: isBest ? 'var(--color-active-text)' : 'var(--color-text-secondary)' }}>
                    {r2 !== null ? Number(r2).toFixed(2) : '—'}
                  </td>
                  <td style={{ padding: '8px 14px', color: 'var(--color-text-secondary)' }}>
                    {acc !== null ? `${Number(acc).toFixed(1)}%` : '—'}
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
