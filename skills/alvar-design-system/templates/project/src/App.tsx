import * as React from "react";
import { Moon, Sun, Sparkles, Info } from "lucide-react";
import { Stack, Cluster, Grid } from "@/primitives";
import {
  Button,
  Card,
  CardTitle,
  CardDescription,
  Input,
  Badge,
  Alert,
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components";

/**
 * Demo surface for the Alvar Design System.
 * Everything here uses the layout primitives (Stack / Cluster / Grid) and
 * semantic-token utilities only, so it themes cleanly in light and dark.
 */
export default function App() {
  const [dark, setDark] = React.useState(false);

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-5xl px-[var(--space-gutter)] py-[var(--space-section)]">
        <Stack gap={16}>
          <Cluster justify="between">
            <Stack gap={2}>
              <h1 className="text-4xl">__APP_NAME__</h1>
              <p className="max-w-[var(--measure)] text-muted-foreground">
                Built with the Alvar Design System: warm, editorial, token-driven.
              </p>
            </Stack>
            <Button
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              aria-label="Toggle colour theme"
            >
              {dark ? <Sun /> : <Moon />}
            </Button>
          </Cluster>

          <Stack gap={4}>
            <CardTitle>Actions</CardTitle>
            <Cluster gap={3}>
              <Button>Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="danger">Danger</Button>
              <Button>
                <Sparkles /> With icon
              </Button>
            </Cluster>
          </Stack>

          <Grid min="16rem" gap={6}>
            <Card variant="outline">
              <Stack gap={2}>
                <CardTitle>Outline</CardTitle>
                <CardDescription>
                  The default card. Separated by space, not chrome.
                </CardDescription>
              </Stack>
            </Card>
            <Card variant="elevated">
              <Stack gap={2}>
                <CardTitle>Elevated</CardTitle>
                <CardDescription>
                  Soft, low-contrast shadow for genuine layering.
                </CardDescription>
              </Stack>
            </Card>
            <Card variant="flat">
              <Stack gap={2}>
                <CardTitle>Flat</CardTitle>
                <CardDescription>A quiet surface tint with no border.</CardDescription>
              </Stack>
            </Card>
          </Grid>

          <Grid min="18rem" gap={6}>
            <Card>
              <Stack gap={4}>
                <CardTitle>Inputs</CardTitle>
                <Input placeholder="Standard field" />
                <Input intent="agentic" placeholder="Ask anything…" />
              </Stack>
            </Card>
            <Card>
              <Stack gap={4}>
                <CardTitle>Badges</CardTitle>
                <Cluster gap={2}>
                  <Badge>Neutral</Badge>
                  <Badge variant="primary">Primary</Badge>
                  <Badge variant="success">Success</Badge>
                  <Badge variant="danger">Danger</Badge>
                  <Badge variant="soft">Soft</Badge>
                  <Badge variant="outline">Outline</Badge>
                </Cluster>
              </Stack>
            </Card>
          </Grid>

          <Alert intent="info" icon={<Info />} title="Heads up">
            Semantic colour resolves through tokens, so this alert flips with the theme.
          </Alert>

          <Dialog>
            <DialogTrigger asChild>
              <Button variant="secondary">Open dialog</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogTitle>A focused moment</DialogTitle>
              <DialogDescription>
                Modals use a blurred scrim and an emphasized entrance. Keep them rare
                and purposeful.
              </DialogDescription>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="ghost">Cancel</Button>
                </DialogClose>
                <DialogClose asChild>
                  <Button>Confirm</Button>
                </DialogClose>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </Stack>
      </div>
    </div>
  );
}
