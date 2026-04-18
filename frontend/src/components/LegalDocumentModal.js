import React, { useEffect } from 'react';
import { getLegalDocument } from './legalDocuments';

function LegalDocumentModal({ documentId, onClose }) {
  const legalDocument = getLegalDocument(documentId);

  useEffect(() => {
    if (!legalDocument) {
      return undefined;
    }

    const previousOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = 'hidden';

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [legalDocument, onClose]);

  if (!legalDocument) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[100] bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-5xl max-h-[92vh] overflow-hidden rounded-3xl bg-white shadow-2xl border border-slate-200">
        <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div>
            <h2 className="text-lg md:text-xl font-semibold text-slate-900">{legalDocument.title}</h2>
            <p className="text-sm text-slate-500">Review without leaving your current screen.</p>
          </div>
          <div className="flex items-center gap-3">
            <a
              href={legalDocument.path}
              target="_blank"
              rel="noreferrer"
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Open in new tab
            </a>
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            >
              Close
            </button>
          </div>
        </div>

        <div className="bg-slate-100 p-3">
          <iframe
            title={legalDocument.title}
            src={legalDocument.path}
            className="h-[72vh] w-full rounded-2xl border border-slate-200 bg-white"
          />
        </div>
      </div>
    </div>
  );
}

export default LegalDocumentModal;
