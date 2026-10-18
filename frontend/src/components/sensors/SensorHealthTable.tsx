import React, { useState } from 'react';
import { Search, Filter, ShieldCheck, AlertTriangle, AlertOctagon } from 'lucide-react';
import { StationDetail } from '../../types';
import { Badge } from '../common/Badge';

interface SensorHealthTableProps {
  stations: StationDetail[];
  selectedStationId: string | null;
  onSelectStation: (station: StationDetail) => void;
  statusFilter: string;
  onStatusFilterChange: (status: string) => void;
}

export const SensorHealthTable: React.FC<SensorHealthTableProps> = ({
  stations,
  selectedStationId,
  onSelectStation,
  statusFilter,
  onStatusFilterChange,
}) => {
  const [search, setSearch] = useState('');

  const filtered = stations.filter((s) => {
    const matchesStatus = statusFilter
      ? s.status.toLowerCase() === statusFilter.toLowerCase()
      : true;
    const matchesSearch =
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.district.toLowerCase().includes(search.toLowerCase()) ||
      s.station_id.toLowerCase().includes(search.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Controls Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          flexWrap: 'wrap',
        }}
      >
        {/* Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--color-surface-alt)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '6px 12px',
            width: '280px',
          }}
        >
          <Search size={14} color="var(--color-text-muted)" />
          <input
            type="text"
            placeholder="Search station or district..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              border: 'none',
              background: 'transparent',
              outline: 'none',
              width: '100%',
              fontSize: '12px',
            }}
          />
        </div>

        {/* Status Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => onStatusFilterChange('')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: !statusFilter ? 'var(--color-primary)' : 'var(--color-surface)',
              color: !statusFilter ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            All ({stations.length})
          </button>
          <button
            onClick={() => onStatusFilterChange('OK')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: statusFilter === 'OK' ? 'var(--color-primary)' : 'var(--color-surface)',
              color: statusFilter === 'OK' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            OK
          </button>
          <button
            onClick={() => onStatusFilterChange('watch')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: statusFilter === 'watch' ? 'var(--color-primary)' : 'var(--color-surface)',
              color: statusFilter === 'watch' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            Watch
          </button>
          <button
            onClick={() => onStatusFilterChange('suspect')}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 500,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: statusFilter === 'suspect' ? 'var(--color-primary)' : 'var(--color-surface)',
              color: statusFilter === 'suspect' ? '#FFFFFF' : 'var(--color-text-secondary)',
            }}
          >
            Suspect
          </button>
        </div>
      </div>

      {/* Table */}
      <div
        style={{
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden',
          backgroundColor: 'var(--color-surface)',
          maxHeight: '380px',
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
                Station & District
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Status
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Observed PM2.5
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                IDW Expected
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Residual
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Z-Score
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600 }}>
                Persistence
              </th>
              <th style={{ padding: '10px 14px', color: 'var(--color-th-text)', fontWeight: 600, width: '30%' }}>
                Diagnostic Reason
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                  No stations match your filter criteria.
                </td>
              </tr>
            ) : (
              filtered.map((st) => {
                const isSelected = st.station_id === selectedStationId;
                let badgeVariant: 'active' | 'warning' | 'expired' | 'neutral' = 'neutral';
                let Icon = ShieldCheck;

                if (st.status.toLowerCase() === 'ok') {
                  badgeVariant = 'active';
                  Icon = ShieldCheck;
                } else if (st.status.toLowerCase() === 'watch') {
                  badgeVariant = 'warning';
                  Icon = AlertTriangle;
                } else if (st.status.toLowerCase() === 'suspect') {
                  badgeVariant = 'expired';
                  Icon = AlertOctagon;
                }

                return (
                  <tr
                    key={st.station_id}
                    onClick={() => onSelectStation(st)}
                    style={{
                      borderBottom: '1px solid var(--color-border-light)',
                      backgroundColor: isSelected ? 'var(--color-onboard-bg)' : 'transparent',
                      cursor: 'pointer',
                      transition: 'background-color 0.1s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) e.currentTarget.style.backgroundColor = 'var(--color-row-hover)';
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--color-heading)' }}>
                        {st.name}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                        {st.district} • {st.agency}
                      </div>
                    </td>

                    <td style={{ padding: '10px 14px' }}>
                      <Badge variant={badgeVariant} size="sm">
                        <Icon size={12} />
                        {st.status.toUpperCase()}
                      </Badge>
                    </td>

                    <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                      {st.observed_pm25 !== null ? `${st.observed_pm25} µg/m³` : '—'}
                    </td>

                    <td style={{ padding: '10px 14px', color: 'var(--color-text-secondary)' }}>
                      {st.expected_pm25 !== null ? `${st.expected_pm25} µg/m³` : '—'}
                    </td>

                    <td
                      style={{
                        padding: '10px 14px',
                        fontWeight: 600,
                        color:
                          st.residual_pm25 !== null && Math.abs(st.residual_pm25) > 25
                            ? 'var(--color-warning-text)'
                            : 'var(--color-text-secondary)',
                      }}
                    >
                      {st.residual_pm25 !== null ? `${st.residual_pm25 > 0 ? '+' : ''}${st.residual_pm25}` : '—'}
                    </td>

                    <td style={{ padding: '10px 14px', color: 'var(--color-text-secondary)' }}>
                      {st.z_score !== null ? st.z_score : '—'}
                    </td>

                    <td style={{ padding: '10px 14px', color: 'var(--color-text-secondary)' }}>
                      {st.hours_persistent > 0 ? `${st.hours_persistent}h` : '0h'}
                    </td>

                    <td style={{ padding: '10px 14px', color: 'var(--color-text-muted)', fontSize: '11px' }}>
                      {st.reasons || 'Normal tracking within spatial tolerance'}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
