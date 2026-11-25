import { lazy, Suspense } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';

const ContactDetailsPage = lazy(() => import('./pages/ContactDetailsPage').then((module) => ({ default: module.ContactDetailsPage })));
const ContactsPage = lazy(() => import('./pages/ContactsPage').then((module) => ({ default: module.ContactsPage })));
const CreateContactPage = lazy(() => import('./pages/CreateContactPage').then((module) => ({ default: module.CreateContactPage })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })));
const EditContactPage = lazy(() => import('./pages/EditContactPage').then((module) => ({ default: module.EditContactPage })));
const OCRPage = lazy(() => import('./pages/OCRPage').then((module) => ({ default: module.OCRPage })));
const AzureOCRPage = lazy(() => import('./pages/AzureOCRPage').then((module) => ({ default: module.AzureOCRPage })));
const VCFReaderPage = lazy(() => import('./pages/VCFReaderPage').then((module) => ({ default: module.VCFReaderPage })));

export default function App() {
  return (
    <Suspense fallback={<Box className="loading-state"><CircularProgress /></Box>}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="contacts" element={<ContactsPage />} />
          <Route path="contacts/create" element={<CreateContactPage />} />
          <Route path="contacts/edit/:id" element={<EditContactPage />} />
          <Route path="contacts/:id" element={<ContactDetailsPage />} />
          <Route path="ocr" element={<OCRPage />} />
          <Route path="azure-ocr" element={<AzureOCRPage />} />
          <Route path="vcf" element={<VCFReaderPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
