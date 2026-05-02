import { type PropsWithChildren } from 'react'
import { cx } from './cx'

export function Container(props: PropsWithChildren<{ className?: string }>) {
  return <div className={cx('vb-container', props.className)}>{props.children}</div>
}

export function Section(props: PropsWithChildren<{ className?: string; id?: string }>) {
  return (
    <section id={props.id} className={cx('vb-section', props.className)}>
      {props.children}
    </section>
  )
}

export function Card(props: PropsWithChildren<{ className?: string }>) {
  return <div className={cx('vb-card', props.className)}>{props.children}</div>
}

export function Button(
  props: PropsWithChildren<{
    className?: string
    variant?: 'primary' | 'ghost' | 'soft'
    onClick?: () => void
    type?: 'button' | 'submit'
    disabled?: boolean
  }>
) {
  const v = props.variant ?? 'primary'
  return (
    <button
      type={props.type ?? 'button'}
      disabled={props.disabled}
      onClick={props.onClick}
      className={cx('vb-btn', `vb-btn--${v}`, props.className)}
    >
      {props.children}
    </button>
  )
}

export function Badge(props: PropsWithChildren<{ className?: string }>) {
  return <span className={cx('vb-badge', props.className)}>{props.children}</span>
}

