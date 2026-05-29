import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/ui/theme-provider";

export function ThemeToggle() {
  const { resolvedTheme, toggle } = useTheme();
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label="Toggle theme"
      title={resolvedTheme === "dark" ? "Switch to light" : "Switch to dark"}
    >
      {resolvedTheme === "dark" ? <Sun /> : <Moon />}
    </Button>
  );
}
