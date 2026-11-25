import { api } from './axios';
import type { Contact, ContactInput } from '../types/contact';

export async function getContacts(): Promise<Contact[]> {
  const { data } = await api.get<Contact[]>('/contacts');
  return data;
}

export async function getContactById(id: string): Promise<Contact> {
  const { data } = await api.get<Contact>(`/contacts/${encodeURIComponent(id)}`);
  return data;
}

export async function createContact(payload: ContactInput): Promise<Contact> {
  const { data } = await api.post<Contact>('/contacts', payload);
  return data;
}

export async function updateContact(id: string, payload: ContactInput): Promise<Contact> {
  const { data } = await api.put<Contact>(`/contacts/${encodeURIComponent(id)}`, payload);
  return data;
}

export async function deleteContact(id: string): Promise<void> {
  await api.delete(`/contacts/${encodeURIComponent(id)}`);
}
