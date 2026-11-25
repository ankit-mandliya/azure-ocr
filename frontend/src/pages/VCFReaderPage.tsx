
import { useMemo, useRef, useState, type DragEvent } from 'react';
import {
  Alert, Box, Button, Card, CardContent, CircularProgress, FormControl, Grid,
  InputLabel, LinearProgress, MenuItem, Select, Stack, Typography,
} from '@mui/material';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import ContactPageRoundedIcon from '@mui/icons-material/ContactPageRounded';
import { ContactForm } from '../components/forms/ContactForm';
import { getErrorMessage } from '../api/axios';
import { previewVCF, type VCFContact } from '../api/vcfApi';
import { useContacts, useCreateContact } from '../hooks/useContacts';
import type { ContactInput } from '../types/contact';

const maxFileSize = 10 * 1024 * 1024;

const splitFullName = (fullName: string | null) => {
  const parts = (fullName ?? '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return { first_name: null, last_name: null };
  return {
    first_name: parts[0],
    last_name: parts.length > 1 ? parts.slice(1).join(' ') : null,
  };
};

const toContactInput = (contact: VCFContact): ContactInput => ({
  ...splitFullName(contact.full_name),
  email: contact.email,
  contact_number: contact.phone,
  company_name: contact.company,
  job_title: contact.job_title,
  website: contact.website,
  address: contact.address,
});

export function VCFReaderPage() {
  const fileInput = useRef<HTMLInputElement>(null);

  const [dragging, setDragging] = useState(false);
  const [contacts, setContacts] = useState<VCFContact[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [fileName, setFileName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const create = useCreateContact();
  const existingContacts = useContacts();
  const [savedIndices, setSavedIndices] = useState<Set<number>>(new Set());

  const preview = contacts[selectedIndex] ? toContactInput(contacts[selectedIndex]) : null;

  const duplicateWarning = useMemo(() => {
    if (!preview) return null;
    const duplicate = existingContacts.data?.find((contact) =>
      (preview.email && contact.email?.toLowerCase() === preview.email.toLowerCase())
      || (preview.contact_number && contact.contact_number?.replace(/\D/g, '') === preview.contact_number.replace(/\D/g, ''))
    );
    return duplicate ? 'A contact with the same email or phone number may already exist.' : null;
  }, [existingContacts.data, preview]);

  const processFile = async (file?: File) => {
    if (!file) return;

    setError(null);
    setContacts([]);
    setSelectedIndex(0);
    setSavedIndices(new Set());
    setUploadProgress(0);

    if (!file.name.toLowerCase().endsWith('.vcf')) {
      setSelectedFile(null);
      setFileName('');
      setError('Please upload a valid VCF file.');
      return;
    }

    if (file.size > maxFileSize) {
      setSelectedFile(null);
      setFileName('');
      setError('The VCF file exceeds the 10 MB upload limit.');
      return;
    }

    setSelectedFile(file);
    setFileName(file.name);
    setBusy(true);

    try {
      const result = await previewVCF(file, setUploadProgress);
      setContacts(result.contacts);
      setSelectedIndex(0);
      setUploadProgress(100);
      if (!result.contacts.length) {
        setError('No contact information found in this VCF file.');
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    void processFile(event.dataTransfer.files[0]);
  };

  const saveReviewedContact = (values: ContactInput) => {
    if (savedIndices.has(selectedIndex)) return;
    create.mutate(values, {
      onSuccess: () => {
        setSavedIndices((current) => new Set(current).add(selectedIndex));
      },
    });
  };

  return (
    <Box className="page-wrap">
      <Box className="page-heading">
        <Box>
          <Typography className="eyebrow">
            SMART CONTACT IMPORTER
          </Typography>
          <Typography variant="h1">
            Import VCF contact
          </Typography>
          <Typography className="page-subtitle">
            Upload a VCF file to extract, review, and save contact details.
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={2.5} sx={{ alignItems: 'stretch' }}>
        <Grid size={{ xs: 12, md: 5 }}>
          <Card className="content-card upload-card">
            <CardContent>
              <Typography variant="h2" sx={{ mb: 0.5 }}>
                Upload VCF file
              </Typography>

              <Typography className="section-subtitle" sx={{ mb: 2.5 }}>
                Select a .vcf contact file from your device.
              </Typography>

              <Box
                className={`drop-zone ${dragging ? 'dragging' : ''}`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => fileInput.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    fileInput.current?.click();
                  }
                }}
              >
                <Box className="upload-icon">
                  <CloudUploadOutlinedIcon />
                </Box>

                <Typography variant="h3">
                  Drag your VCF file here
                </Typography>

                <Typography className="section-subtitle">
                  or click to choose a file
                </Typography>

                <Typography className="file-hint">
                  VCF · max 10 MB
                </Typography>

                <input
                  ref={fileInput}
                  hidden
                  type="file"
                  accept=".vcf,text/vcard,text/x-vcard"
                  onChange={(event) =>
                    void processFile(event.target.files?.[0])
                  }
                />
              </Box>

              <Button
                fullWidth
                variant="contained"
                startIcon={<ContactPageRoundedIcon />}
                disabled={!selectedFile || busy}
                onClick={() => void processFile(selectedFile ?? undefined)}
                sx={{ mt: 2 }}
              >
                {busy ? 'Reading contact…' : 'Read VCF again'}
              </Button>

              {fileName && (
                <Typography className="file-selected">
                  Selected: {fileName}
                </Typography>
              )}

              {busy && (
                <Stack sx={{ mt: 2 }} gap={1}>
                  <Stack sx={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={18} />
                    <Typography className="section-subtitle">
                      Uploading and extracting contact information… {uploadProgress}%
                    </Typography>
                  </Stack>
                  <LinearProgress variant="determinate" value={uploadProgress} />
                </Stack>
              )}

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 7 }}>
          <Card className="content-card preview-card">
            <CardContent>
              <Box className="section-heading">
                <Box>
                  <Typography variant="h2">
                    Review contact details
                  </Typography>
                  <Typography className="section-subtitle">
                    {preview
                      ? 'Check and correct the extracted information before saving.'
                      : 'Your contact preview will appear here after uploading.'}
                  </Typography>
                </Box>
              </Box>

              {preview ? (
                <>
                  {contacts.length > 1 && (
                    <FormControl fullWidth sx={{ mb: 2.5 }}>
                      <InputLabel id="vcf-contact-label">Extracted contact</InputLabel>
                      <Select
                        labelId="vcf-contact-label"
                        value={selectedIndex}
                        label="Extracted contact"
                        onChange={(event) => setSelectedIndex(Number(event.target.value))}
                      >
                        {contacts.map((contact, index) => (
                          <MenuItem key={index} value={index}>
                            {contact.full_name || contact.email || contact.phone || `Contact ${index + 1}`}
                            {savedIndices.has(index) ? ' — Saved' : ''}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                  <Typography className="section-subtitle" sx={{ mb: 2 }}>
                    {contacts.length} contact{contacts.length === 1 ? '' : 's'} extracted
                  </Typography>
                  {duplicateWarning && <Alert severity="warning" sx={{ mb: 2 }}>{duplicateWarning}</Alert>}
                  {savedIndices.has(selectedIndex) && <Alert severity="success" sx={{ mb: 2 }}>This contact has been saved.</Alert>}
                  <ContactForm
                    initialValues={preview}
                    submitLabel={savedIndices.has(selectedIndex) ? 'Saved' : 'Save contact'}
                    busy={create.isPending || savedIndices.has(selectedIndex)}
                    onSubmit={saveReviewedContact}
                    error={
                      create.error
                        ? getErrorMessage(create.error)
                        : null
                    }
                  />
                </>
              ) : (
                <Box className="preview-placeholder">
                  <ContactPageRoundedIcon />
                  <Typography variant="h3">
                    Nothing to review yet
                  </Typography>
                  <Typography>
                    Upload a VCF file to see the contact details.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
