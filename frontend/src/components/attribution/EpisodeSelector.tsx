import React from 'react';
import { Calendar, Flame, AlertCircle } from 'lucide-react';
import { EpisodeSummary } from '../../types';
import { Badge } from '../common/Badge';

interface EpisodeSelectorProps {
  episodes: EpisodeSummary[];
  selectedEpisodeId: number;
  onSelectEpisode: (id: number) => void;
  selectedSeason: string;
  onSelectSeason: (season: string) => void;
}

export const EpisodeSelector: React.FC<EpisodeSelectorProps> = ({
  episodes,
  selectedEpisodeId,
  onSelectEpisode,
  selectedSeason,
  onSelectSeason,
}) => {
  const filtered = selectedSeason
    ? episodes.filter((e) => e.season === selectedSeason)
    : episodes;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Filters Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Season:
          </span>
          <button
            onClick={() => onSelectSeason('')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: !selectedSeason ? 'var(--color-primary)' : 'var(--color-surface)',
              color: !selectedSeason ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            All Windows ({episodes.length})
          </button>
          <button
            onClick={() => onSelectSeason('2021')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: selectedSeason === '2021' ? 'var(--color-primary)' : 'var(--color-surface)',
              color: selectedSeason === '2021' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            2021 Season
          </button>
          <button
            onClick={() => onSelectSeason('2023')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: selectedSeason === '2023' ? 'var(--color-primary)' : 'var(--color-surface)',
              color: selectedSeason === '2023' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            2023 Season
          </button>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          Click an episode to view 5,000-draw attribution intervals
        </div>
      </div>

      {/* Episode Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '12px',
        }}
      >
        {filtered.map((ep) => {
          const isSelected = ep.episode_id === selectedEpisodeId;
          return (
            <div
              key={ep.episode_id}
              onClick={() => onSelectEpisode(ep.episode_id)}
              style={{
                backgroundColor: isSelected ? 'var(--color-surface)' : 'var(--color-surface)',
                border: isSelected
                  ? '2px solid var(--color-primary)'
                  : '1px solid var(--color-border-card)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                cursor: 'pointer',
                boxShadow: isSelected ? 'var(--shadow-md)' : 'var(--shadow-xs)',
                transition: 'all 0.15s ease',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      backgroundColor: isSelected ? 'var(--color-primary)' : 'var(--color-surface-alt)',
                      color: isSelected ? '#FFFFFF' : 'var(--color-primary)',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-xs)',
                    }}
                  >
                    EPISODE {ep.episode_id}
                  </span>
                  {ep.diwali_window === 1 && (
                    <Badge variant="warning" size="sm">
                      <Flame size={11} />
                      Diwali Window
                    </Badge>
                  )}
                </div>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 500 }}>
                  {ep.duration_days} Days
                </span>
              </div>

              <h4
                style={{
                  fontSize: '14px',
                  fontWeight: 600,
                  color: 'var(--color-heading)',
                  marginBottom: '8px',
                }}
              >
                {ep.title}
              </h4>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '12px',
                  color: 'var(--color-text-secondary)',
                  marginBottom: '12px',
                }}
              >
                <Calendar size={13} color="var(--color-text-muted)" />
                <span>
                  {ep.start} to {ep.end}
                </span>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '8px',
                  padding: '8px 10px',
                  backgroundColor: 'var(--color-surface-alt)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '11px',
                }}
              >
                <div>
                  <span style={{ color: 'var(--color-text-muted)' }}>Peak PM2.5:</span>{' '}
                  <strong style={{ color: '#B23A3A' }}>{Math.round(ep.peak_pm25)} µg/m³</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--color-text-muted)' }}>Mean PM2.5:</span>{' '}
                  <strong style={{ color: 'var(--color-heading)' }}>{Math.round(ep.mean_pm25)} µg/m³</strong>
                </div>
              </div>

              <div
                style={{
                  marginTop: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingTop: '8px',
                  borderTop: '1px solid var(--color-border-light)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Lead Source:</span>
                  <Badge sourceKey={ep.dominant_source} size="sm">
                    {ep.dominant_source.replace('_', ' ')} ({Math.round(ep.dominant_share)}%)
                  </Badge>
                </div>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    color:
                      ep.dominant_label === 'Supported'
                        ? 'var(--color-active-text)'
                        : 'var(--color-warning-text)',
                  }}
                >
                  {ep.dominant_label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
