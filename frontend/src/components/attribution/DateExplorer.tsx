import React from 'react';
import { Calendar } from 'lucide-react';
import { Card } from '../common/Card';

interface DateExplorerProps {
  onDateSelect: (date: string) => void;
  selectedDate: string;
  loading: boolean;
  noEpisodeMessage?: string;
}

export const DateExplorer: React.FC<DateExplorerProps> = ({
  onDateSelect,
  selectedDate,
  loading,
  noEpisodeMessage = "No severe pollution episode recorded for this date.",
}) => {
  return (
    <Card title="Date-Based Attribution Lookup" subtitle="Select a date to map it to its containing smog episode and examine the attribution ledger.">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '8px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-heading)', fontWeight: 600 }}>
          <Calendar size={18} />
          <span>Select Date:</span>
        </div>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => onDateSelect(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface)',
            color: 'var(--color-text)',
            fontSize: '14px',
            fontFamily: 'inherit',
            cursor: 'pointer',
          }}
        />
        {loading && <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Mapping date to episode...</span>}
      </div>
    </Card>
  );
};
