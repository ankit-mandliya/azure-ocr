import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createContact,
  deleteContact,
  getContactById,
  getContacts,
  updateContact,
} from '../api/contactApi';
import type { ContactInput } from '../types/contact';

export const contactsKey = ['contacts'] as const;

export function useContacts() {
  return useQuery({ queryKey: contactsKey, queryFn: getContacts });
}

export function useContact(id: string) {
  return useQuery({ queryKey: [...contactsKey, id], queryFn: () => getContactById(id), enabled: !!id });
}

export function useCreateContact() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: createContact,
    onSuccess: () => client.invalidateQueries({ queryKey: contactsKey }),
  });
}

export function useUpdateContact() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ContactInput }) => updateContact(id, payload),
    onSuccess: (contact) => {
      client.setQueryData([...contactsKey, contact.id], contact);
      return client.invalidateQueries({ queryKey: contactsKey });
    },
  });
}

export function useDeleteContact() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: deleteContact,
    onSuccess: () => client.invalidateQueries({ queryKey: contactsKey }),
  });
}
