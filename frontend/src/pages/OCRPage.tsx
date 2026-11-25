import { useRef, useState, type DragEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Card, CardContent, CircularProgress, FormControl, Grid,
  InputLabel, MenuItem, Select, Stack, Typography,
} from '@mui/material';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import DocumentScannerRoundedIcon from '@mui/icons-material/DocumentScannerRounded';
import { ContactForm } from '../components/forms/ContactForm';
import { getErrorMessage } from '../api/axios';
import { previewCard } from '../api/ocrApi';
import { useCreateContact } from '../hooks/useContacts';
import type { ContactInput, OCRPreview } from '../types/contact';

const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
const maxFileSize = 10 * 1024 * 1024;

export function OCRPage() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [language, setLanguage] = useState('latin');
  const [preview, setPreview] = useState<OCRPreview | null>(null);
  const [fileName, setFileName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const create = useCreateContact();

  const processFile = async (file?: File) => {
    if (!file) return;
    setError(null);
    setPreview(null);
    if (!allowedTypes.includes(file.type)) {
      setSelectedFile(null);
      setFileName('');
      setError('Choose a JPG, PNG, or WEBP image.');
      return;
    }
    if (file.size > maxFileSize) {
      setSelectedFile(null);
      setFileName('');
      setError('The image exceeds the 10 MB upload limit.');
      return;
    }
    setSelectedFile(file);
    setFileName(file.name);
    setBusy(true);
    try {
      const result = await previewCard(file, language);
      setPreview(result);
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
    create.mutate(values, { onSuccess: (contact) => navigate(`/contacts/${contact.id}`) });
  };

  return (
    <Box className="page-wrap">
      <Box className="page-heading"><Box><Typography className="eyebrow">SMART CARD SCANNER</Typography><Typography variant="h1">Scan a business card</Typography><Typography className="page-subtitle">Extract, check, and correct the details before saving.</Typography></Box></Box>
      <Grid container spacing={2.5} sx={{ alignItems: 'stretch' }}>
        <Grid size={{ xs: 12, md: 5 }}>
          <Card className="content-card upload-card"><CardContent>
            <Typography variant="h2" sx={{ mb: 0.5 }}>Upload card image</Typography>
            <Typography className="section-subtitle" sx={{ mb: 2.5 }}>Use a clear, well-lit image for the best results.</Typography>
            <Box
              className={`drop-zone ${dragging ? 'dragging' : ''}`}
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => fileInput.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') fileInput.current?.click(); }}
            >
              <Box className="upload-icon"><CloudUploadOutlinedIcon /></Box>
              <Typography variant="h3">Drag your card here</Typography>
              <Typography className="section-subtitle">or click to choose a file</Typography>
              <Typography className="file-hint">JPG, PNG or WEBP · max 10 MB</Typography>
              <input ref={fileInput} hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => void processFile(event.target.files?.[0])} />
            </Box>
            <FormControl fullWidth sx={{ mt: 2.5 }}>
              <InputLabel id="ocr-language-label">Text language</InputLabel>
              <Select labelId="ocr-language-label" value={language} label="Text language" onChange={(event) => setLanguage(event.target.value)}>
                <MenuItem value="latin">English / Latin</MenuItem>
                <MenuItem value="devanagari">Hindi / Devanagari</MenuItem>
                <MenuItem value="arabic">Arabic</MenuItem>
                <MenuItem value="tamil">Tamil</MenuItem>
                <MenuItem value="telugu">Telugu</MenuItem>
              </Select>
            </FormControl>
            <Button fullWidth variant="contained" startIcon={<DocumentScannerRoundedIcon />} disabled={!selectedFile || busy} onClick={() => void processFile(selectedFile ?? undefined)} sx={{ mt: 2 }}>
              {busy ? 'Reading card…' : 'Run OCR again'}
            </Button>
            {fileName && <Typography className="file-selected">Selected: {fileName}</Typography>}
            {busy && <Stack sx={{ mt: 2, display: 'flex', flexDirection: 'row', alignItems: 'center', gap: 1.2 }}><CircularProgress size={18} /><Typography className="section-subtitle">Extracting text from your card…</Typography></Stack>}
            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          </CardContent></Card>
        </Grid>
        <Grid size={{ xs: 12, md: 7 }}>
          <Card className="content-card preview-card"><CardContent>
            <Box className="section-heading"><Box><Typography variant="h2">Review extracted details</Typography><Typography className="section-subtitle">{preview ? 'Make any corrections, then save your contact.' : 'Your editable preview will appear here after scanning.'}</Typography></Box>
              {preview?.overall_confidence !== null && preview && <Box className="confidence-badge">{Math.round(preview.overall_confidence * 100)}% confidence</Box>}
            </Box>
            {preview ? (
              <>
                {preview.warnings.length > 0 && <Alert severity="warning" sx={{ mb: 2 }}>{preview.warnings.join(' ')}</Alert>}
                <ContactForm
                  initialValues={preview}
                  submitLabel="Save contact"
                  busy={create.isPending}
                  onSubmit={saveReviewedContact}
                  error={create.error ? getErrorMessage(create.error) : null}
                />
              </>
            ) : <Box className="preview-placeholder"><DocumentScannerRoundedIcon /><Typography variant="h3">Nothing to review yet</Typography><Typography>Upload a business card to see the fields we found.</Typography></Box>}
          </CardContent></Card>
        </Grid>
      </Grid>
    </Box>
  );
}
