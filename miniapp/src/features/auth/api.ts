import { api } from '@/shared/api/endpoints';

export async function exchangeInitData(initData: string) {
  return api.auth.telegram(initData);
}
