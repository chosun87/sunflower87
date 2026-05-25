import { confirmDialog } from '@/assets/ts/PrimeReact';
import type { ConfirmDialogProps } from 'primereact/confirmdialog';

export interface DialogOptions extends ConfirmDialogProps {
  message: ConfirmDialogProps['message'];
}

/**
 * 단순 알림/안내용 다이얼로그 (확인 버튼 1개)
 */
export const showNotice = ({
  header = '안내',
  icon = 'pi pi-info-circle',
  message,
  acceptLabel = '확인',
  accept = () => {},
  ...props
}: DialogOptions) => {
  confirmDialog({
    header,
    icon,
    message,
    acceptLabel,
    rejectClassName: 'hidden',
    accept,
    ...props,
  });
};

/**
 * 확인/취소가 필요한 다이얼로그
 */
export const showConfirm = ({
  header = '확인',
  icon = 'pi pi-exclamation-triangle',
  message,
  acceptLabel = '확인',
  rejectLabel = '취소',
  accept = () => {},
  reject = () => {},
  ...props
}: DialogOptions) => {
  confirmDialog({
    header,
    icon,
    message,
    acceptLabel,
    rejectLabel,
    accept,
    reject,
    ...props,
  });
};

/**
 * 오류 안내용 다이얼로그
 */
export const showError = (error: unknown, header = '오류 안내') => {
  let message = '알 수 없는 오류가 발생했습니다.';

  if (typeof error === 'string') {
    message = error;
  } else if (error instanceof Error) {
    message = error.message;
  } else if (error && typeof error === 'object' && 'message' in error) {
    message = String((error as Record<string, unknown>).message);
  } else if (error) {
    try {
      message = JSON.stringify(error);
    } catch {
      // JSON.stringify 실패 시 기본 메시지 유지
    }
  }

  showNotice({
    header,
    icon: 'pi pi-times-circle',
    message,
    acceptClassName: 'p-button-danger',
  });
};
