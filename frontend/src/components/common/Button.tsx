import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon,
  children,
  style = {},
  disabled,
  className = '',
  ...props
}) => {
  let bg = 'var(--color-primary)';
  let color = '#FFFFFF';
  let border = '1px solid var(--color-primary)';

  if (variant === 'secondary') {
    bg = 'var(--color-onboard-bg)';
    color = 'var(--color-onboard-text)';
    border = '1px solid var(--color-secondary-navy)';
  } else if (variant === 'outline') {
    bg = 'transparent';
    color = 'var(--color-btn-secondary-text)';
    border = '1px solid var(--color-btn-secondary-border)';
  } else if (variant === 'ghost') {
    bg = 'transparent';
    color = 'var(--color-text-secondary)';
    border = '1px solid transparent';
  }

  const padding = size === 'sm' ? '6px 12px' : size === 'lg' ? '10px 20px' : '8px 16px';
  const fontSize = size === 'sm' ? '12px' : size === 'lg' ? '15px' : '13px';

  return (
    <button
      className={className}
      disabled={disabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        padding,
        fontSize,
        fontWeight: 500,
        borderRadius: 'var(--radius-sm)',
        backgroundColor: bg,
        color,
        border,
        boxShadow: variant === 'primary' ? 'var(--shadow-xs)' : 'none',
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s ease',
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          if (variant === 'primary') e.currentTarget.style.backgroundColor = 'var(--color-primary-hover)';
          if (variant === 'outline' || variant === 'ghost') e.currentTarget.style.backgroundColor = 'var(--color-surface-alt)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          if (variant === 'primary') e.currentTarget.style.backgroundColor = 'var(--color-primary)';
          if (variant === 'outline' || variant === 'ghost') e.currentTarget.style.backgroundColor = 'transparent';
        }
      }}
      {...props}
    >
      {icon && <span style={{ display: 'flex', alignItems: 'center' }}>{icon}</span>}
      {children}
    </button>
  );
};
