// frontend/src/hooks/useToast.tsx
import { useEffect, useState } from "react";
import { Toast, ToastActionElement, ToastProps } from "@/components/ui/toast";

type ToasterToast = ToastProps & {
  id: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: ToastActionElement;
};

const TOAST_LIMIT = 5;
const TOAST_REMOVE_DELAY = 1000;

type ToasterToastState = {
  toasts: ToasterToast[];
};

let count = 0;

function generateToastId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER;
  return count.toString();
}

const toastState = { toasts: [] } as ToasterToastState;
const listeners: Array<(state: ToasterToastState) => void> = [];

function addToast(toast: ToasterToast) {
  const nextState = {
    ...toastState,
    toasts: [...toastState.toasts, toast].slice(0, TOAST_LIMIT),
  };

  toastState.toasts = nextState.toasts;
  listeners.forEach((listener) => listener(nextState));
}

function dismissToast(toastId: string) {
  const nextState = {
    ...toastState,
    toasts: toastState.toasts.filter((t) => t.id !== toastId),
  };

  toastState.toasts = nextState.toasts;
  listeners.forEach((listener) => listener(nextState));
}

export function useToast() {
  const [state, setState] = useState<ToasterToastState>(toastState);

  useEffect(() => {
    listeners.push(setState);

    return () => {
      const index = listeners.indexOf(setState);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }, [state]);

  return {
    toasts: state.toasts,
    toast: (props: Omit<ToasterToast, "id">) => {
      const id = generateToastId();
      const toast = { ...props, id };
      addToast(toast);

      return {
        id,
        dismiss: () => dismissToast(id),
        update: (props: ToasterToast) => {
          const nextState = {
            ...toastState,
            toasts: toastState.toasts.map((t) =>
              t.id === id ? { ...t, ...props } : t
            ),
          };

          toastState.toasts = nextState.toasts;
          listeners.forEach((listener) => listener(nextState));
        },
      };
    },
    dismiss: (toastId: string) => dismissToast(toastId),
  };
}
