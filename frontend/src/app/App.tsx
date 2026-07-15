import Providers from "./providers";
import AppRoutes from "../routes";
import "../assets/style.css";

export default function App() {
  return (
    <Providers>
      <AppRoutes />
    </Providers>
  );
}
