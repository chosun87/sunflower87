import { useContext } from "react";
import { AuthContext, AuthTimerContext } from "../context/AuthContext";

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const useAuthTimer = () => {
  const context = useContext(AuthTimerContext);
  if (context === undefined) {
    throw new Error("useAuthTimer must be used within an AuthProvider");
  }
  return context;
};
