import React from 'react';
import { getLegalDocument } from './legalDocuments';

function LegalDocumentLink({ document, onOpen, className = '', children }) {
  const legalDocument = getLegalDocument(document);

  if (!legalDocument) {
    return null;
  }

  if (!onOpen) {
    return (
      <a
        href={legalDocument.path}
        target="_blank"
        rel="noreferrer"
        className={className}
      >
        {children || legalDocument.label}
      </a>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onOpen(legalDocument.id)}
      className={`appearance-none bg-transparent border-0 p-0 font-inherit text-inherit ${className}`}
    >
      {children || legalDocument.label}
    </button>
  );
}

export default LegalDocumentLink;
