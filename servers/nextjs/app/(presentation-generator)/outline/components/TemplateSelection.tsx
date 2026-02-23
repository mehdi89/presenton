"use client";
import React, { useEffect } from "react";
import { useLayout } from "../../context/LayoutContext";
import TemplateLayouts from "./TemplateLayouts";

import { Template } from "../types/index";

interface TemplateSelectionProps {
  selectedTemplate: Template | null;
  onSelectTemplate: (template: Template) => void;
}

const TemplateSelection: React.FC<TemplateSelectionProps> = ({
  selectedTemplate,
  onSelectTemplate
}) => {
  const {
    getLayoutsByTemplateID,
    getTemplateSetting,
    getAllTemplateIDs,
    loading
  } = useLayout();


  const templates: Template[] = React.useMemo(() => {
    const allTemplateIDs = getAllTemplateIDs();
    if (allTemplateIDs.length === 0) return [];

    // Filter to only built-in templates (exclude custom templates)
    const builtInTemplates: Template[] = allTemplateIDs
      .filter((templateID: string) => !templateID.toLowerCase().startsWith("custom-"))
      .map(templateID => {
        const settings = getTemplateSetting(templateID);
        return {
          id: templateID,
          name: templateID,
          description: settings?.description || `${templateID} presentation templates`,
          ordered: settings?.ordered || false,
          default: settings?.default || false,
        };
      });

    // Sort templates to put default first, then by name
    return builtInTemplates.sort((a, b) => {
      if (a.default && !b.default) return -1;
      if (!a.default && b.default) return 1;
      return a.name.localeCompare(b.name);
    });
  }, [getAllTemplateIDs, getTemplateSetting]);

  // Auto-select first template when templates are loaded
  useEffect(() => {
    if (templates.length > 0 && !selectedTemplate) {
      const defaultTemplate = templates.find(g => g.default) || templates[0];
      const slides = getLayoutsByTemplateID(defaultTemplate.id);

      onSelectTemplate({
        ...defaultTemplate,
        slides: slides,
      });
    }
  }, [templates, selectedTemplate, onSelectTemplate]);
  useEffect(() => {
    if (loading) {
      return;
    }
    const existingScript = document.querySelector(
      'script[src*="tailwindcss.com"]'
    );
    if (!existingScript) {
      const script = document.createElement("script");
      script.src = "https://cdn.tailwindcss.com";
      script.async = true;
      document.head.appendChild(script);
    }

  }, []);


  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-4 rounded-lg border border-gray-200 bg-gray-50 animate-pulse">
              <div className="h-4 bg-gray-200 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 rounded mb-3"></div>
              <div className="grid grid-cols-3 gap-2 mb-3">
                {[1, 2, 3].map((j) => (
                  <div key={j} className="aspect-video bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-8">
          <h5 className="text-lg font-medium mb-2 text-gray-700">
            No Templates Available
          </h5>
          <p className="text-gray-600 text-sm">
            No presentation templates could be loaded. Please try refreshing the page.
          </p>
        </div>
      </div>
    );
  }

  const handleTemplateSelection = (template: Template) => {
    const slides = getLayoutsByTemplateID(template.id);
    onSelectTemplate({
      ...template,
      slides: slides,
    });
  }

  return (
    <div className="space-y-8 mb-4">
      {/* In Built Templates */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">In Built Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {templates.map((template) => (
            <TemplateLayouts
              key={template.id}
              template={template}
              onSelectTemplate={handleTemplateSelection}
              selectedTemplate={selectedTemplate}
            />
          ))}
        </div>
      </div>

    </div>
  );
};

export default TemplateSelection; 