import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "../components/layouts/AppLayout";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
}
