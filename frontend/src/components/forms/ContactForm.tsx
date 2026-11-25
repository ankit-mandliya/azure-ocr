import { useEffect } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Alert, Box, Button, Grid, Stack, TextField } from '@mui/material';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import type { ContactInput } from '../../types/contact';

const schema = z.object({
  first_name: z.string().max(100),
  last_name: z.string().max(100),
  email: z.string().email('Enter a valid email address').or(z.literal('')),
  contact_number: z.string().max(30).regex(/^[+\d\s().-]*$/, 'Enter a valid phone number'),
  company_name: z.string().max(200),
  job_title: z.string().max(150),
  website: z.string().url('Enter a valid URL including https://').or(z.literal('')),
  address: z.string().max(500),
}).refine(
  (value) => [value.first_name, value.last_name, value.email, value.contact_number, value.company_name].some((item) => item.trim()),
  { message: 'Add at least a name, email, phone number, or company.', path: ['first_name'] },
);

type FormValues = z.infer<typeof schema>;

const fields: Array<{ name: keyof ContactInput; label: string; required?: boolean; span?: number }> = [
  { name: 'first_name', label: 'First name', span: 6 },
  { name: 'last_name', label: 'Last name', span: 6 },
  { name: 'email', label: 'Email', span: 6 },
  { name: 'contact_number', label: 'Phone', span: 6 },
  { name: 'company_name', label: 'Company', span: 6 },
  { name: 'job_title', label: 'Designation', span: 6 },
  { name: 'website', label: 'Website', span: 12 },
  { name: 'address', label: 'Address', span: 12 },
];

interface ContactFormProps {
  initialValues: ContactInput;
  submitLabel: string;
  busy?: boolean;
  onSubmit: (values: ContactInput) => void;
  onCancel?: () => void;
  error?: string | null;
}

export function ContactForm({ initialValues, submitLabel, busy = false, onSubmit, onCancel, error }: ContactFormProps) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      first_name: initialValues.first_name ?? '',
      last_name: initialValues.last_name ?? '',
      email: initialValues.email ?? '',
      contact_number: initialValues.contact_number ?? '',
      company_name: initialValues.company_name ?? '',
      job_title: initialValues.job_title ?? '',
      website: initialValues.website ?? '',
      address: initialValues.address ?? '',
    },
  });

  useEffect(() => reset({
    first_name: initialValues.first_name ?? '',
    last_name: initialValues.last_name ?? '',
    email: initialValues.email ?? '',
    contact_number: initialValues.contact_number ?? '',
    company_name: initialValues.company_name ?? '',
    job_title: initialValues.job_title ?? '',
    website: initialValues.website ?? '',
    address: initialValues.address ?? '',
  }), [initialValues, reset]);

  const submit = (values: FormValues) => {
    onSubmit({
      first_name: values.first_name.trim() || null,
      last_name: values.last_name.trim() || null,
      email: values.email.trim() || null,
      contact_number: values.contact_number.trim() || null,
      company_name: values.company_name.trim() || null,
      job_title: values.job_title.trim() || null,
      website: values.website.trim() || null,
      address: values.address.trim() || null,
    });
  };

  return (
    <Box component="form" onSubmit={handleSubmit(submit)} noValidate>
      <Grid container spacing={2.25}>
        {fields.map(({ name, label, span = 6 }) => (
          <Grid key={name} size={{ xs: 12, sm: span }}>
            <TextField
              {...register(name)}
              fullWidth
              label={label}
              error={!!errors[name]}
              helperText={errors[name]?.message}
              multiline={name === 'address'}
              minRows={name === 'address' ? 3 : undefined}
              type={name === 'email' ? 'email' : 'text'}
              placeholder={name === 'website' ? 'https://example.com' : undefined}
            />
          </Grid>
        ))}
      </Grid>
      {errors.first_name?.message && <Alert severity="warning" sx={{ mt: 2 }}>{errors.first_name.message}</Alert>}
      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      <Stack sx={{ mt: 3, display: 'flex', flexDirection: 'row', gap: 1.5, justifyContent: 'flex-end' }}>
        {onCancel && <Button onClick={onCancel} color="inherit">Cancel</Button>}
        <Button type="submit" variant="contained" disabled={busy}>{busy ? 'Saving…' : submitLabel}</Button>
      </Stack>
    </Box>
  );
}
