"use client";

import React from 'react';
import { marked } from 'marked';

interface MarkdownTextProps {
  children: string | undefined | null;
  className?: string;
  style?: React.CSSProperties;
  as?: keyof JSX.IntrinsicElements;
}

/**
 * Component that renders markdown text as HTML
 * Preserves all styling and className props
 */
const MarkdownText: React.FC<MarkdownTextProps> = ({
  children,
  className = '',
  style = {},
  as: Component = 'span'
}) => {
  if (!children) return null;

  // Check if the content contains markdown syntax
  const hasMarkdown = /(\*\*|__|~~|\*|_|`|\[.*\]\(.*\))/.test(children);

  if (!hasMarkdown) {
    // No markdown detected, render as plain text
    return React.createElement(Component, { className, style }, children);
  }

  // Parse markdown to HTML (inline parsing to avoid wrapping in <p> tags)
  const html = marked.parseInline(children);

  return React.createElement(Component, {
    className,
    style,
    dangerouslySetInnerHTML: { __html: html }
  });
};

export default MarkdownText;