export const LEGAL_DOCUMENTS = {
  privacy: {
    id: 'privacy',
    label: 'Privacy Policy',
    title: 'Privacy Policy',
    path: '/privacy',
  },
  terms: {
    id: 'terms',
    label: 'Terms of Service',
    title: 'Terms of Service',
    path: '/terms',
  },
  security: {
    id: 'security',
    label: 'Security',
    title: 'Security',
    path: '/security',
  },
};

export function getLegalDocument(documentId) {
  return LEGAL_DOCUMENTS[documentId] || null;
}
