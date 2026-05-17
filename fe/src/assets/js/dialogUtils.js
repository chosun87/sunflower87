import { confirmDialog } from './PrimeReact'

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
}) => {
  confirmDialog({
    header,
    icon,
    message,
    acceptLabel,
    rejectClassName: 'hidden',
    accept,
    ...props,
  })
}

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
}) => {
  confirmDialog({
    header,
    icon,
    message,
    acceptLabel,
    rejectLabel,
    accept,
    reject,
    ...props,
  })
}

/**
 * 오류 안내용 다이얼로그
 */
export const showError = (error, header = '오류 안내') => {
  const message =
    typeof error === 'string' ? error : error?.message || JSON.stringify(error)

  showNotice({
    header,
    icon: 'pi pi-times-circle',
    message,
    acceptClassName: 'p-button-danger',
  })
}
