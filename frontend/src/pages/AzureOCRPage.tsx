import { useEffect, useRef, useState, type DragEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Card, CardContent, CircularProgress, Chip, Grid,
  Stack, TextField, Typography,
} from '@mui/material';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import DocumentScannerRoundedIcon from '@mui/icons-material/DocumentScannerRounded';
import { useMutation, useQuery } from '@tanstack/react-query';
import { getErrorMessage } from '../api/axios';
import {
  extractAzureBusinessCard,
  getAzureOCRStatus,
  saveAzureContact,
  type AzureReviewedContact,
} from '../api/azureOCRApi';
import type { AzureBusinessCard, ExtractedValue } from '../types/azureOCR';

const allowedTypes = ['image/jpeg', 'image/png'];
const maxFileSize = 10 * 1024 * 1024;

const firstValue = (values: ExtractedValue[]) => values[0]?.value ?? '';

function confidenceLabel(value: number | null) {
  if (value === null) return null;
  return `${Math.round(value * 100)}%`;
}

export function AzureOCRPage() {
  const fileInput = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [card, setCard] = useState<AzureBusinessCard | null>(null);
  const [values, setValues] = useState<AzureReviewedContact>({
    first_name: null,
    last_name: null,
    email: null,
    contact_number: null,
    company_name: null,
    department: null,
    address: null,
    job_title: null,
    website: null,
  });

  const status = useQuery({ queryKey: ['azure-ocr-status'], queryFn: getAzureOCRStatus });
  const extract = useMutation({ mutationFn: extractAzureBusinessCard });
  const save = useMutation({ mutationFn: saveAzureContact });

  useEffect(() => {
    if (!card) return;
    setValues({
      first_name: card.first_name,
      last_name: card.last_name,
      email: firstValue(card.emails),
      contact_number: firstValue(card.mobile_phones) || firstValue(card.work_phones),
      company_name: card.company_name,
      department: card.department,
      address: firstValue(card.addresses),
      job_title: card.job_title,
      website: firstValue(card.websites),
    });
  }, [card]);

  const selectFile = (selected?: File) => {
    if (!selected) return;
    setError(null);
    setCard(null);
    if (!allowedTypes.includes(selected.type)) {
      setFile(null);
      setFileName('');
      setError('Choose a JPG or PNG image.');
      return;
    }
    if (selected.size > maxFileSize) {
      setFile(null);
      setFileName('');
      setError(`The image exceeds the ${maxFileSize / 1024 / 1024} MB upload limit.`);
      return;
    }
    setFile(selected);
    setFileName(selected.name);
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files[0]);
  };

  const runExtraction = () => {
    if (!file) return;
    setError(null);
    setCard(null);
    extract.mutate(file, {
      onSuccess: (result) => {
        if (result.cards.length === 0) {
          setError('No business card was detected in the image.');
          return;
        }
        setCard(result.cards[0]);
      },
      onError: (requestError) => setError(getErrorMessage(requestError)),
    });
  };

  const update = (field: keyof AzureReviewedContact, value: string) => {
    setValues((current) => ({ ...current, [field]: value.trim() || null }));
  };

  const saveContact = () => {
    if (save.isPending) return;
    setError(null);
    save.mutate(values, {
      onSuccess: (contact) => navigate(`/contacts/${contact.id}`),
      onError: (requestError) => setError(getErrorMessage(requestError)),
    });
  };

  const confidence = (extracted: ExtractedValue[] | undefined) =>
    extracted?.length ? confidenceLabel(extracted[0].confidence) : null;

  return (
    <Box className="page-wrap">
      <Box className="page-heading">
        <Box>
          <Typography className="eyebrow">MICROSOFT AZURE AI</Typography>
          <Typography variant="h1">Azure OCR</Typography>
          <Typography className="page-subtitle">Extract business card information using Microsoft Azure AI.</Typography>
        </Box>
      </Box>

      {status.data && !status.data.configured && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Azure OCR is not configured. Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY to enable extraction.
        </Alert>
      )}

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 5 }}>
          <Card className="content-card">
            <CardContent>
              <Typography variant="h2">Upload business card</Typography>
              <Typography className="section-subtitle" sx={{ mt: 0.5, mb: 2.5 }}>Use a clear JPG or PNG image.</Typography>
              <Box
                className={`drop-zone ${dragging ? 'dragging' : ''}`}
                onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => fileInput.current?.click()}
                role="button"
                tabIndex={0}
              >
                <Box className="upload-icon"><CloudUploadOutlinedIcon /></Box>
                <Typography variant="h3">{fileName || 'Drag your card here'}</Typography>
                <Typography className="section-subtitle">or click to choose a file</Typography>
                <Typography className="file-hint">JPG or PNG · max 10 MB</Typography>
                <input
                  ref={fileInput}
                  hidden
                  type="file"
                  accept="image/jpeg,image/png"
                  onChange={(event) => selectFile(event.target.files?.[0])}
                />
              </Box>
              {fileName && (
                <Stack direction="row" sx={{ mt: 2 }} spacing={1}>
                  <Button color="inherit" onClick={() => { setFile(null); setFileName(''); setCard(null); }}>Remove</Button>
                  <Button variant="contained" startIcon={<DocumentScannerRoundedIcon />} disabled={extract.isPending} onClick={runExtraction}>
                    {extract.isPending ? 'Extracting…' : 'Extract'}
                  </Button>
                </Stack>
              )}
              {extract.isPending && <Stack direction="row" sx={{ mt: 2, alignItems: 'center', gap: 1 }}><CircularProgress size={18} /><Typography>Analyzing with Azure…</Typography></Stack>}
              {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 7 }}>
          <Card className="content-card">
            <CardContent>
              <Typography variant="h2">Review extracted details</Typography>
              {card ? (
                <Box sx={{ mt: 2 }}>
                  <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap' }}>
                    {confidence(card.emails) && <Chip label={`Email ${confidence(card.emails)}`} size="small" color="success" />}
                    {confidence(card.mobile_phones) && <Chip label={`Mobile ${confidence(card.mobile_phones)}`} size="small" color="warning" />}
                    {confidence(card.addresses) && <Chip label={`Address ${confidence(card.addresses)}`} size="small" />}
                  </Stack>
                  <Grid container spacing={2}>
                    {([
                      ['first_name', 'First name'],
                      ['last_name', 'Last name'],
                      ['email', 'Email'],
                      ['contact_number', 'Mobile / work phone'],
                      ['company_name', 'Company'],
                      ['department', 'Department'],
                      ['job_title', 'Job title'],
                      ['website', 'Website'],
                      ['address', 'Address'],
                    ] as Array<[keyof AzureReviewedContact, string]>).map(([field, label]) => (
                      <Grid key={field} size={{ xs: 12, sm: field === 'address' ? 12 : 6 }}>
                        <TextField
                          fullWidth
                          label={label}
                          value={values[field] ?? ''}
                          onChange={(event) => update(field, event.target.value)}
                          multiline={field === 'address'}
                          minRows={field === 'address' ? 2 : undefined}
                          type={field === 'email' ? 'email' : 'text'}
                        />
                      </Grid>
                    ))}
                  </Grid>
                  {save.error && <Alert severity="error" sx={{ mt: 2 }}>{getErrorMessage(save.error)}</Alert>}
                  <Stack direction="row" justifyContent="flex-end" sx={{ mt: 3 }}>
                    <Button variant="contained" disabled={save.isPending} onClick={saveContact}>
                      {save.isPending ? 'Saving…' : 'Save contact'}
                    </Button>
                  </Stack>
                </Box>
              ) : (
                <Box className="preview-placeholder">
                  <DocumentScannerRoundedIcon />
                  <Typography variant="h3">Nothing to review yet</Typography>
                  <Typography>Upload a business card and extract its details.</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
