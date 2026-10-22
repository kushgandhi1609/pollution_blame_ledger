import React, { useState } from 'react';
import { Calendar } from 'lucide-react';
import { Card } from '../common/Card';
import { EpisodeDetail, EpisodeSummary } from '../../types';
import { EvidenceLabelsTable } from './EvidenceLabelsTable';
import { AttributionIntervalChart } from './AttributionIntervalChart';
import { api } from '../../services/api';

interface DateAttributionViewProps {
  episodes: EpisodeSummary[];
}

export const DateAttributionView: React.FC<DateAttributionViewProps> = ({ episodes }) => {
  const [selectedDate, setSelectedDate] = useState('');
  const [episodeDetail, setEpisodeDetail] = useState<EpisodeDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDateSelect = async (date: string) => {
    setSelectedDate(date);
    if (!date) return;

    setLoading(true);
    setError(null);
    try {
      const detail = await api.getEpisodeByDate(date);
      if (detail) {
        setEpisodeDetail(detail);
      } else {
        setEpisodeDetail(null);
        setError("No severe pollution episode recorded for this date.");
      }
    } catch (err: any) {
      console.error('Error fetching attribution by date:', err);
      setError(err.message || "Failed to retrieve attribution data.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <Card title="Date-Based Attribution Lookup" subtitle="Select a date to map it to its containing smog episode and examine the attribution ledger.">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '8px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-heading)', fontWeight: 600 }}>
            <Calendar size={18} />
            <span>Select Date:</span>
          </div>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => handleDateSelect(e.target.value)}
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

      {loading ? (
        <Card>
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            Loading 5,000-draw Monte Carlo attribution ledger...
          </div>
        </Card>
      ) : error ? (
        <Card>
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            {error}
          </div>
        </Card>
      ) : episodeDetail ? (
        <>
          <Card>
            <div style={{ marginBottom: '16px', color: 'var(--color-heading)', fontWeight: 600 }}>
              {episodeDetail.summary.title}
            </div>
            <AttributionIntervalChart
              attribution={episodeDetail.attribution}
              episodeTitle={episodeDetail.summary.title}
            />
          </Card>

          <Card>
            <EvidenceLabelsTable labels={episodeDetail.evidence_labels} />
          </Card>
        </>
      ) : (
        <Card>
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            Select a date to examine attribution intervals.
          </div>
        </Card>
      )}
    </div>
  );
};
