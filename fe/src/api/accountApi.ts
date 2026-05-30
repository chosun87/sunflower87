import { del, get, post, put } from './index';

export interface AccountCreateData {
  acc_cd: string;
  acc_nm: string;
  acc_company_nm: string;
  dt_opened?: string;
  acc_order?: number;
}

export interface AccountUpdateData {
  acc_nm?: string;
  acc_company_nm?: string;
  dt_opened?: string;
  acc_order?: number;
}

export const getAccounts = (includeDeleted: boolean = false) => {
  return get(`/api/accounts?include_deleted=${includeDeleted}`);
};

export const getAccount = (accCd: string) => {
  return get(`/api/accounts/${accCd}`);
};

export const createAccount = (data: AccountCreateData) => {
  return post('/api/accounts', data);
};

export const updateAccount = (accCd: string, data: AccountUpdateData) => {
  return put(`/api/accounts/${accCd}`, data);
};

export const deleteAccount = (accCd: string) => {
  return del(`/api/accounts/${accCd}`);
};
