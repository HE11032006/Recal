import { Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import Onboarding from "./pages/Onboarding";
import Today from "./pages/Today";
import Saved from "./pages/Saved";
import Profile from "./pages/Profile";

export default function App() {
  const hasProfile = localStorage.getItem("recal:onboarded") === "true";

  return (
    <Routes>
      <Route
        path="/onboarding"
        element={<Onboarding />}
      />
      <Route
        path="/"
        element={hasProfile ? <AppShell /> : <Navigate to="/onboarding" replace />}
      >
        <Route index element={<Today />} />
        <Route path="saved" element={<Saved />} />
        <Route path="profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
