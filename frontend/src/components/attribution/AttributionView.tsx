import React from 'react';
import { Card } from '../common/Card';
import { EpisodeDetail, EpisodeSummary } from '../../types';
import { EpisodeSelector } from './EpisodeSelector';
import { AttributionIntervalChart } from './AttributionIntervalChart';
import { EvidenceLabelsTable } from './EvidenceLabelsTable';
import { EpisodeTimeseriesChart } from './EpisodeTimeseriesChart';

interface AttributionViewProps {
  episodes: EpisodeSummary[];
  selectedEpisodeId: number;
  onSelectEpisode: (id: number) => void;
  selectedSeason: string;
  onSelectSeason: (season: string) => void;
  episodeDetail: EpisodeDetail | null;
  loading: boolean;
}

export const AttributionView: React.FC<AttributionViewProps> = ({
  episodes,
  selectedEpisodeId,
  onSelectEpisode,
  selectedSeason,
  onSelectSeason,
  episodeDetail,
  loading,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Episode Selector */}
      <Card
        title="Severe Pollution Episodes Catalog"
        subtitle="Cataloged high-particulate smog episodes across 2021 and 2023 post-monsoon and winter seasons."
      >
        <EpisodeSelector
          episodes={episodes}
          selectedEpisodeId={selectedEpisodeId}
          onSelectEpisode={onSelectEpisode}
          selectedSeason={selectedSeason}
          onSelectSeason={onSelectSeason}
        />
      </Card>

      {/* 2. Detailed Episode Attribution Breakdown */}
      {loading ? (
        <Card>
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            Loading 5,000-draw Monte Carlo attribution ledger...
          </div>
        </Card>
      ) : episodeDetail ? (
        <>
          <Card>
            <AttributionIntervalChart
              attribution={episodeDetail.attribution}
              episodeTitle={episodeDetail.summary.title}
            />
          </Card>

          <Card>
            <EvidenceLabelsTable labels={episodeDetail.evidence_labels} />
          </Card>

          <Card>
            <EpisodeTimeseriesChart
              timeseries={episodeDetail.timeseries}
              episodeTitle={episodeDetail.summary.title}
            />
          </Card>
        </>
      ) : (
        <Card>
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            Select an episode above to examine attribution intervals.
          </div>
        </Card>
      )}
    </div>
  );
};
