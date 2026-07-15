import type { ReactNode } from "react";
import { GlobalStateProvider } from "../store/globalState";

export default function Providers({ children }: { children: ReactNode }) {
  return <GlobalStateProvider>{children}</GlobalStateProvider>;
}
