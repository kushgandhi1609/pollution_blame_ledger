import React, { useState } from 'react';
import { Card } from '../common/Card';
import { SensorValidationReport, StationDetail } from '../../types';
import { StationMap } from './StationMap';
import { SensorHealthTable } from './SensorHealthTable';
import { SensorBenchmarkCard } from './SensorBenchmarkCard';
import { Modal } from '../common/Modal';
import { Badge } from '../common/Badge';

interface SensorsViewProps {
  stations: StationDetail[];
  validation: SensorValidationReport | null;
  loading: boolean;
}

export const SensorsView: React.FC<SensorsViewProps> = ({
  stations,
  validation,
  loading,
}) => {
  const [selectedStation, setSelectedStation] = useState<StationDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 1. Spatial Telemetry Map */}
      <Card
        title="Delhi-NCR Continuous Air Quality Monitoring Network"
        subtitle="72 continuous ambient monitoring stations mapped across Delhi, Haryana, and UP boundaries with real-time IDW spatial consistency checks."
      >
        <StationMap
          stations={stations}
          selectedStationId={selectedStation?.station_id || null}
          onSelectStation={(st) => setSelectedStation(st)}
          statusFilter={statusFilter}
        />
      </Card>

      {/* 2. Validation Benchmark Card */}
      <SensorBenchmarkCard validation={validation} />

      {/* 3. Sensor Health Diagnostics Table */}
      <Card
        title="Neighborhood Consistency & Residual Telemetry"
        subtitle="Stations evaluated with Inverse-Distance Weighting (k=4, 40km corridor) standardizing spatial deviations against historical variance."
      >
        <SensorHealthTable
          stations={stations}
          selectedStationId={selectedStation?.station_id || null}
          onSelectStation={(st) => setSelectedStation(st)}
          statusFilter={statusFilter}
          onStatusFilterChange={(s) => setStatusFilter(s)}
        />
      </Card>

      {/* Station Detail Modal */}
      <Modal
        isOpen={!!selectedStation}
        onClose={() => setSelectedStation(null)}
        title={selectedStation?.name || 'Station Diagnostics'}
        subtitle={`${selectedStation?.district} • ${selectedStation?.agency} (${selectedStation?.station_id})`}
      >
        {selectedStation && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Badge
                variant={
                  selectedStation.status.toLowerCase() === 'suspect'
                    ? 'expired'
                    : selectedStation.status.toLowerCase() === 'watch'
                    ? 'warning'
                    : 'active'
                }
              >
                Health Status: {selectedStation.status.toUpperCase()}
              </Badge>
              <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                Coords: [{selectedStation.lat.toFixed(4)}, {selectedStation.lon.toFixed(4)}]
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '12px',
                backgroundColor: 'var(--color-surface-alt)',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                fontSize: '12px',
              }}
            >
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>Observed PM2.5:</span>{' '}
                <strong>{selectedStation.observed_pm25 !== null ? `${selectedStation.observed_pm25} µg/m³` : 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>IDW Expected PM2.5:</span>{' '}
                <strong>{selectedStation.expected_pm25 !== null ? `${selectedStation.expected_pm25} µg/m³` : 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>Spatial Residual:</span>{' '}
                <strong>{selectedStation.residual_pm25 !== null ? `${selectedStation.residual_pm25} µg/m³` : 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>Z-Score Deviation:</span>{' '}
                <strong>{selectedStation.z_score !== null ? selectedStation.z_score : 'N/A'}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>Consecutive Persistent Drift:</span>{' '}
                <strong>{selectedStation.hours_persistent} Hours</strong>
              </div>
              <div>
                <span style={{ color: 'var(--color-text-muted)' }}>24h Neighborhood Tracking (r):</span>{' '}
                <strong>{selectedStation.corr24h !== null ? selectedStation.corr24h : 'N/A'}</strong>
              </div>
            </div>

            <div style={{ fontSize: '12px', lineHeight: 1.6 }}>
              <h5 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-heading)', marginBottom: '4px' }}>
                Diagnostic Telemetry Assessment:
              </h5>
              <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
                {selectedStation.reasons || 'The station tracks closely with its geographic nearest neighbors within normal variance.'}
              </p>
            </div>

            <div
              style={{
                backgroundColor: 'var(--color-onboard-bg)',
                border: '1px solid var(--color-secondary-navy)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 14px',
                fontSize: '11px',
                color: 'var(--color-onboard-text)',
              }}
            >
              <strong>Policy Safeguard:</strong> The label 'suspect' is strictly used as an observational flag. Sensor telemetry is never altered or deleted unilaterally without ground maintenance verification.
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
