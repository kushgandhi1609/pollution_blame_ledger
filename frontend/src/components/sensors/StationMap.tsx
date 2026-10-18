import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { StationDetail } from '../../types';
import { Badge } from '../common/Badge';

interface StationMapProps {
  stations: StationDetail[];
  selectedStationId: string | null;
  onSelectStation: (station: StationDetail) => void;
  statusFilter: string;
}

export const StationMap: React.FC<StationMapProps> = ({
  stations,
  selectedStationId,
  onSelectStation,
  statusFilter,
}) => {
  const filtered = statusFilter
    ? stations.filter((s) => s.status.toLowerCase() === statusFilter.toLowerCase())
    : stations;

  // Center on Delhi-NCR
  const center: [number, number] = [28.6139, 77.209];

  const getMarkerColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'suspect':
        return { stroke: '#B23A3A', fill: '#FCE8E8', radius: 8 };
      case 'watch':
        return { stroke: '#D97706', fill: '#FFF7ED', radius: 7 };
      case 'ok':
        return { stroke: '#1E6B45', fill: '#E5F3EC', radius: 6 };
      default:
        return { stroke: '#7C8DA0', fill: '#F2F6FB', radius: 5 };
    }
  };

  return (
    <div style={{ height: '480px', width: '100%', position: 'relative', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
      <MapContainer
        center={center}
        zoom={10}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', backgroundColor: 'var(--color-surface-alt)' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {filtered.map((st) => {
          const lat = st.lat || st.latitude;
          const lon = st.lon || st.longitude;
          if (!lat || !lon) return null;

          const styling = getMarkerColor(st.status);
          const isSelected = st.station_id === selectedStationId;

          return (
            <CircleMarker
              key={st.station_id}
              center={[lat, lon]}
              radius={isSelected ? styling.radius + 3 : styling.radius}
              pathOptions={{
                color: styling.stroke,
                fillColor: styling.fill,
                fillOpacity: 0.9,
                weight: isSelected ? 3 : 1.5,
              }}
              eventHandlers={{
                click: () => onSelectStation(st),
              }}
            >
              <Popup>
                <div style={{ fontSize: '12px', minWidth: '180px', fontFamily: 'var(--font-family)' }}>
                  <div style={{ fontWeight: 700, color: 'var(--color-heading)', marginBottom: '4px' }}>
                    {st.name}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
                    {st.district} • {st.agency}
                  </div>

                  <div style={{ marginBottom: '8px' }}>
                    <Badge
                      variant={
                        st.status === 'suspect'
                          ? 'expired'
                          : st.status === 'watch'
                          ? 'warning'
                          : 'active'
                      }
                      size="sm"
                    >
                      Status: {st.status.toUpperCase()}
                    </Badge>
                  </div>

                  <div style={{ fontSize: '11px', lineHeight: 1.6 }}>
                    <div>
                      Observed PM2.5: <strong>{st.observed_pm25 !== null ? `${st.observed_pm25} µg/m³` : 'N/A'}</strong>
                    </div>
                    <div>
                      IDW Expected: <strong>{st.expected_pm25 !== null ? `${st.expected_pm25} µg/m³` : 'N/A'}</strong>
                    </div>
                    <div>
                      Spatial Residual: <strong>{st.residual_pm25 !== null ? `${st.residual_pm25 > 0 ? '+' : ''}${st.residual_pm25} µg/m³` : 'N/A'}</strong>
                    </div>
                    <div>
                      Z-Score: <strong>{st.z_score !== null ? st.z_score : 'N/A'}</strong>
                    </div>
                  </div>

                  <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid var(--color-border)', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    {st.reasons || 'Normal tracking within spatial tolerance'}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Map Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          zIndex: 500,
          backgroundColor: 'var(--color-surface)',
          padding: '8px 14px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--color-border-card)',
          boxShadow: 'var(--shadow-sm)',
          fontSize: '11px',
          display: 'flex',
          gap: '14px',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: '#E5F3EC',
              border: '1.5px solid #1E6B45',
            }}
          />
          <span>OK (Spatial Consensus)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: '#FFF7ED',
              border: '1.5px solid #D97706',
            }}
          />
          <span>Watch (Moderate Drift)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: '#FCE8E8',
              border: '1.5px solid #B23A3A',
            }}
          />
          <span>Suspect (Persistent Deviation)</span>
        </div>
      </div>
    </div>
  );
};
