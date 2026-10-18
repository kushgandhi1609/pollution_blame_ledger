import React from 'react';
import { Card } from '../common/Card';
import { ActionRecommendation, DustDemoResponse } from '../../types';
import { ActionRecommendations } from './ActionRecommendations';
import { DustSimulationPanel } from './DustSimulationPanel';

interface PolicyViewProps {
  actions: ActionRecommendation[];
  dustDemo: DustDemoResponse | null;
  activeEpisodeTitle?: string;
}

export const PolicyView: React.FC<PolicyViewProps> = ({
  actions,
  dustDemo,
  activeEpisodeTitle,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Policy Actions */}
      <Card
        title="Source-to-Action Operational Matrix"
        subtitle={`Prioritized regulatory and civic interventions linked to active source signals for ${activeEpisodeTitle || 'the current episode'}.`}
      >
        <ActionRecommendations actions={actions} episodeTitle={activeEpisodeTitle} />
      </Card>

      {/* 2. Dust Rescheduler & Misting Simulation */}
      <Card
        title="Interactive Intervention Modeling"
        subtitle="Counterfactual simulation demonstrating the exposure-smoothing effects of atmospheric-aware task rescheduling."
      >
        <DustSimulationPanel initialDemo={dustDemo} />
      </Card>
    </div>
  );
};
