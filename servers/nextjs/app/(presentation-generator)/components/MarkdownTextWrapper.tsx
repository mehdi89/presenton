"use client";

import React, { useEffect, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import MarkdownText from './MarkdownText';

interface MarkdownTextWrapperProps {
  children: React.ReactNode;
}

/**
 * Wrapper component that finds and replaces text nodes with MarkdownText components
 * Only processes text in non-edit mode to render markdown as HTML
 */
const MarkdownTextWrapper: React.FC<MarkdownTextWrapperProps> = ({ children }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const processedElements = useRef(new Set<HTMLElement>());
  const rootsRef = useRef<Map<HTMLElement, any>>(new Map());

  useEffect(() => {
    if (!containerRef.current) return;

    const replaceTextElements = () => {
      const container = containerRef.current;
      if (!container) return;

      // Get all elements in the container
      const allElements = container.querySelectorAll('*');

      allElements.forEach((element) => {
        const htmlElement = element as HTMLElement;

        // Skip if already processed or is a React component
        if (
          processedElements.current.has(htmlElement) ||
          htmlElement.classList.contains('markdown-text-processed') ||
          htmlElement.closest('.markdown-text-processed') ||
          htmlElement.closest('.tiptap-text-editor')
        ) {
          return;
        }

        // Skip certain elements
        const skipTags = ['SCRIPT', 'STYLE', 'SVG', 'PATH', 'INPUT', 'TEXTAREA', 'BUTTON', 'SELECT'];
        if (skipTags.includes(htmlElement.tagName)) return;

        // Get direct text content
        const directTextContent = Array.from(htmlElement.childNodes)
          .filter(node => node.nodeType === Node.TEXT_NODE)
          .map(node => node.textContent || '')
          .join('')
          .trim();

        // Check if element has meaningful text content with markdown
        if (!directTextContent || directTextContent.length <= 2) return;

        // Check for markdown patterns
        const hasMarkdown = /(\*\*|__|~~|\*|_|`|\[.*\]\(.*\))/.test(directTextContent);
        if (!hasMarkdown) return;

        // Skip if element has child elements with text
        const hasTextChildren = Array.from(htmlElement.children).some((child) => {
          const childText = (child as HTMLElement).innerText?.trim();
          return childText && childText.length > 1;
        });
        if (hasTextChildren) return;

        // Get all styles and classes
        const allClasses = Array.from(htmlElement.classList);
        const allStyles = htmlElement.getAttribute('style');

        // Create container for MarkdownText
        const markdownContainer = document.createElement(htmlElement.tagName.toLowerCase());
        markdownContainer.style.cssText = allStyles || '';
        markdownContainer.className = allClasses.join(' ') + ' markdown-text-processed';

        // Replace the element
        if (htmlElement.parentNode) {
          htmlElement.parentNode.replaceChild(markdownContainer, htmlElement);
        }

        processedElements.current.add(htmlElement);

        // Render MarkdownText component
        const root = ReactDOM.createRoot(markdownContainer);
        rootsRef.current.set(markdownContainer, root);

        root.render(
          <MarkdownText
            className={allClasses.join(' ')}
            style={allStyles ? {} : undefined}
          >
            {directTextContent}
          </MarkdownText>
        );
      });
    };

    // Replace text elements after DOM is ready
    const timer = setTimeout(replaceTextElements, 100);

    return () => {
      clearTimeout(timer);
      // Clean up React roots
      rootsRef.current.forEach(root => {
        try {
          root.unmount();
        } catch (e) {
          // Ignore unmount errors
        }
      });
      rootsRef.current.clear();
      processedElements.current.clear();
    };
  }, [children]);

  return (
    <div ref={containerRef} className="markdown-text-wrapper">
      {children}
    </div>
  );
};

export default MarkdownTextWrapper;